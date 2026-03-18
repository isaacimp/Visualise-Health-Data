<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: {
    label: string;
    light: number;
    deep: number;
    rem: number;
    awake: number;
  }[] = [];
  export let maxPoints: number = 14;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  // Take the most recent data points (data is already in reverse chronological order from backend)
  $: displayData = data.slice(0, maxPoints).reverse();

  // Stage colors - professional palette matching new theme
  const stageColors = {
    deep: '#0d9488',    // Teal - deepest sleep
    rem: '#7c3aed',     // Purple - REM
    light: '#94a3b8',   // Slate - light sleep
    awake: '#dc2626'    // Red - awake
  };

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 30, right: 100, bottom: 50, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Convert minutes to hours for all stages
    const processedData = displayData.map(d => ({
      label: d.label,
      Deep: d.deep / 60,
      REM: d.rem / 60,
      Light: d.light / 60,
      Awake: d.awake / 60
    }));

    // Stack the data - order matters for visual clarity
    const stack = d3.stack()
      .keys(['Deep', 'REM', 'Light', 'Awake'])
      .order(d3.stackOrderNone)
      .offset(d3.stackOffsetWiggle)  // Creates streamgraph effect
      .value((d: any, key) => d[key] || 0);

    const series = stack(processedData as any);

    // Scales
    const x = d3.scaleLinear()
      .domain([0, processedData.length - 1])
      .range([0, innerWidth]);

    const yExtent = [
      d3.min(series, layer => d3.min(layer, d => d[0])) || 0,
      d3.max(series, layer => d3.max(layer, d => d[1])) || 10
    ];

    const y = d3.scaleLinear()
      .domain(yExtent)
      .range([innerHeight, 0]);

    const colorMap: { [key: string]: string } = {
      'Deep': stageColors.deep,
      'REM': stageColors.rem,
      'Light': stageColors.light,
      'Awake': stageColors.awake
    };

    // Gridlines
    g.append('g')
      .attr('class', 'grid')
      .call(
        d3.axisLeft(y)
          .tickSize(-innerWidth)
          .tickFormat(() => '')
      )
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('.tick line')
        .attr('stroke', '#e5e7eb')
        .attr('stroke-width', 1)
      );

    // Area generator for streamgraph
    const area = d3.area<any>()
      .x((d, i) => x(i))
      .y0(d => y(d[0]))
      .y1(d => y(d[1]))
      .curve(d3.curveCatmullRom);

    // Draw stacked areas (streamgraph)
    g.selectAll('path')
      .data(series)
      .join('path')
        .attr('d', area)
        .attr('fill', d => colorMap[d.key])
        .attr('opacity', 0.85)
        .on('mouseover', function(event, d: any) {
          d3.select(this).attr('opacity', 1);
          const [mouseX] = d3.pointer(event);
          const xIndex = Math.round(x.invert(mouseX));
          const validIndex = Math.max(0, Math.min(processedData.length - 1, xIndex));
          const data = processedData[validIndex];
          const value = data[d.key];

          tooltip
            .style('opacity', 1)
            .html(`
              <strong>${data.label}</strong><br/>
              <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: ${colorMap[d.key]}; border-radius: 2px;"></span>
                <span>${d.key}: ${value.toFixed(1)}h</span>
              </div>
            `)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 28}px`);
        })
        .on('mousemove', function(event, d: any) {
          const [mouseX] = d3.pointer(event);
          const xIndex = Math.round(x.invert(mouseX));
          const validIndex = Math.max(0, Math.min(processedData.length - 1, xIndex));
          const data = processedData[validIndex];
          const value = data[d.key];

          tooltip
            .html(`
              <strong>${data.label}</strong><br/>
              <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: ${colorMap[d.key]}; border-radius: 2px;"></span>
                <span>${d.key}: ${value.toFixed(1)}h</span>
              </div>
            `)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 28}px`);
        })
        .on('mouseout', function() {
          d3.select(this).attr('opacity', 0.85);
          tooltip.style('opacity', 0);
        });

    // X Axis
    const tickCount = Math.floor(innerWidth / 70);
    const everyNth = Math.ceil(displayData.length / tickCount);

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(x)
          .tickValues(processedData.map((_, i) => i).filter((_, i) => i % everyNth === 0))
          .tickFormat((d) => processedData[d as number].label)
          .tickSize(0)
      )
      .call(g => g.select('.domain').attr('stroke', '#e5e7eb'))
      .call(g => g.selectAll('text')
        .attr('fill', '#6b7280')
        .attr('dy', '1em')
        .style('font-size', '11px')
      );

    // Hide Y Axis for streamgraph (centered around middle, values less meaningful)
    // Just show a center reference line
    g.append('line')
      .attr('x1', 0)
      .attr('x2', innerWidth)
      .attr('y1', innerHeight / 2)
      .attr('y2', innerHeight / 2)
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4')
      .attr('opacity', 0.5);

    // Legend
    const legend = svg.append('g')
      .attr('transform', `translate(${width - margin.right + 15},${margin.top})`);

    const legendData = [
      { label: 'Deep Sleep', color: stageColors.deep },
      { label: 'REM Sleep', color: stageColors.rem },
      { label: 'Light Sleep', color: stageColors.light },
      { label: 'Awake', color: stageColors.awake }
    ];

    legendData.forEach((item, i) => {
      const legendRow = legend.append('g')
        .attr('transform', `translate(0,${i * 24})`);

      legendRow.append('rect')
        .attr('width', 14)
        .attr('height', 14)
        .attr('fill', item.color)
        .attr('opacity', 0.9)
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
