<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: {
    label: string;
    start: string;
    end: string;
    light: number;
    deep: number;
    rem: number;
    awake: number;
  }[] = [];
  export let maxPoints: number = 14;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);

  // Stage colors
  const stageColors = {
    awake: '#ef4444',
    light: '#60a5fa',
    deep: '#8b5cf6',
    rem: '#ec4899'
  };

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 80, bottom: 40, left: 80 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Y scale for sleep sessions (one row per night)
    const y = d3.scaleBand()
      .domain(displayData.map(d => d.label))
      .range([0, innerHeight])
      .padding(0.3);

    // Calculate time range for X axis (midnight to midnight)
    const parseTime = (dateStr: string) => new Date(dateStr);

    // Find earliest and latest times to set scale
    let minTime = Infinity;
    let maxTime = -Infinity;

    displayData.forEach(d => {
      const start = parseTime(d.start).getTime();
      const end = parseTime(d.end).getTime();
      if (start < minTime) minTime = start;
      if (end > maxTime) maxTime = end;
    });

    const x = d3.scaleTime()
      .domain([new Date(minTime), new Date(maxTime)])
      .range([0, innerWidth]);

    // Draw timeline bars for each night
    displayData.forEach((d, i) => {
      const yPos = y(d.label)!;
      const barHeight = y.bandwidth();
      const startTime = parseTime(d.start);
      const endTime = parseTime(d.end);

      // Background bar
      g.append('rect')
        .attr('x', x(startTime))
        .attr('y', yPos)
        .attr('width', x(endTime) - x(startTime))
        .attr('height', barHeight)
        .attr('fill', '#f3f4f6')
        .attr('rx', 4);

      // Calculate stage positions (proportional to duration)
      const totalMinutes = d.light + d.deep + d.rem + d.awake;
      let currentX = x(startTime);

      // Draw each stage segment
      const stages = [
        { name: 'light', minutes: d.light, color: stageColors.light },
        { name: 'deep', minutes: d.deep, color: stageColors.deep },
        { name: 'rem', minutes: d.rem, color: stageColors.rem },
        { name: 'awake', minutes: d.awake, color: stageColors.awake }
      ];

      stages.forEach(stage => {
        if (stage.minutes > 0) {
          const proportion = stage.minutes / totalMinutes;
          const segmentWidth = (x(endTime) - x(startTime)) * proportion;

          g.append('rect')
            .attr('x', currentX)
            .attr('y', yPos)
            .attr('width', segmentWidth)
            .attr('height', barHeight)
            .attr('fill', stage.color)
            .attr('opacity', 0.85)
            .on('mouseover', function(event) {
              d3.select(this).attr('opacity', 1);
              tooltip
                .style('opacity', 1)
                .html(`
                  <strong>${d.label}</strong><br/>
                  <span style="color:${stage.color}">■</span> ${stage.name.charAt(0).toUpperCase() + stage.name.slice(1)}: ${(stage.minutes / 60).toFixed(1)}h
                `)
                .style('left', `${event.offsetX + 10}px`)
                .style('top', `${event.offsetY - 28}px`);
            })
            .on('mouseout', function() {
              d3.select(this).attr('opacity', 0.85);
              tooltip.style('opacity', 0);
            });

          currentX += segmentWidth;
        }
      });
    });

    // Y Axis (dates)
    g.append('g')
      .call(d3.axisLeft(y).tickSize(0))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('text')
        .attr('fill', '#374151')
        .style('font-size', '12px')
        .style('font-weight', '500')
      );

    // X Axis (time)
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(x)
          .ticks(6)
          .tickFormat(d => d3.timeFormat('%I:%M %p')(d as Date))
      )
      .call(g => g.select('.domain').attr('stroke', '#e5e7eb'))
      .call(g => g.selectAll('text')
        .attr('fill', '#6b7280')
        .style('font-size', '11px')
      );

    // Legend
    const legend = svg.append('g')
      .attr('transform', `translate(${width - margin.right + 10},${margin.top})`);

    const legendData = [
      { label: 'Light', color: stageColors.light },
      { label: 'Deep', color: stageColors.deep },
      { label: 'REM', color: stageColors.rem },
      { label: 'Awake', color: stageColors.awake }
    ];

    legendData.forEach((item, i) => {
      const legendRow = legend.append('g')
        .attr('transform', `translate(0,${i * 24})`);

      legendRow.append('rect')
        .attr('width', 14)
        .attr('height', 14)
        .attr('fill', item.color)
        .attr('opacity', 0.85)
        .attr('rx', 3);

      legendRow.append('text')
        .attr('x', 20)
        .attr('y', 11)
        .attr('fill', '#374151')
        .style('font-size', '12px')
        .style('font-weight', '500')
        .text(item.label);
    });

    // Tooltip
    d3.select(container).selectAll('.tooltip').remove();
    const tooltip = d3.select(container)
      .append('div')
      .attr('class', 'tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', 'white')
      .style('border', '1px solid #e5e7eb')
      .style('box-shadow', '0 4px 6px -1px rgba(0,0,0,0.1)')
      .style('border-radius', '8px')
      .style('padding', '10px 14px')
      .style('font-size', '13px')
      .style('color', '#111827')
      .style('pointer-events', 'none')
      .style('z-index', '1000');
  }

  onMount(() => {
    observer = new ResizeObserver(() => draw());
    observer.observe(container);
    draw();
  });

  onDestroy(() => {
    observer?.disconnect();
  });

  $: if (displayData) draw();
</script>

<div bind:this={container} style="position: relative; width: 100%; height: 100%;">
  <svg bind:this={svgEl} style="display: block;" />
</div>
