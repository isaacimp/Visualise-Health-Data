<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: { label: string; value: number }[] = [];
  export let color: string = '#8b5cf6';
  export let maxPoints: number = 30;
  export let targetHours: number = 8;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 30, right: 20, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleLinear()
      .domain([0, displayData.length - 1])
      .range([0, innerWidth]);

    // Set Y-axis to start from a reasonable minimum (e.g., 4 hours)
    const minValue = Math.min(4, d3.min(displayData, d => d.value)! - 1);
    const maxValue = Math.max(targetHours + 1, d3.max(displayData, d => d.value)! + 0.5);

    const y = d3.scaleLinear()
      .domain([minValue, maxValue])
      .nice()
      .range([innerHeight, 0]);

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

    // Target line
    g.append('line')
      .attr('x1', 0)
      .attr('x2', innerWidth)
      .attr('y1', y(targetHours))
      .attr('y2', y(targetHours))
      .attr('stroke', '#10b981')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,4')
      .attr('opacity', 0.6);

    g.append('text')
      .attr('x', innerWidth - 5)
      .attr('y', y(targetHours) - 8)
      .attr('fill', '#10b981')
      .attr('text-anchor', 'end')
      .style('font-size', '12px')
      .style('font-weight', '600')
      .text(`Goal: ${targetHours}h`);

    // Area
    const area = d3.area<{ label: string; value: number }>()
      .x((d, i) => x(i))
      .y0(innerHeight)
      .y1(d => y(d.value))
      .curve(d3.curveCatmullRom);

    g.append('path')
      .datum(displayData)
      .attr('fill', color)
      .attr('opacity', 0.2)
      .attr('d', area);

    // Line
    const line = d3.line<{ label: string; value: number }>()
      .x((d, i) => x(i))
      .y(d => y(d.value))
      .curve(d3.curveCatmullRom);

    g.append('path')
      .datum(displayData)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2.5)
      .attr('d', line);

    // Points
    g.selectAll('.dot')
      .data(displayData)
      .join('circle')
        .attr('class', 'dot')
        .attr('cx', (d, i) => x(i))
        .attr('cy', d => y(d.value))
        .attr('r', 4)
        .attr('fill', d => d.value >= targetHours ? '#10b981' : d.value >= targetHours - 1 ? '#f59e0b' : '#ef4444')
        .attr('stroke', 'white')
        .attr('stroke-width', 2)
        .on('mouseover', function(event, d) {
          d3.select(this).attr('r', 6);
          const hours = Math.floor(d.value);
          const minutes = Math.round((d.value - hours) * 60);
          const timeStr = minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
          tooltip
            .style('opacity', 1)
            .html(`<strong>${d.label}</strong><br/>${timeStr}`)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 28}px`);
        })
        .on('mouseout', function() {
          d3.select(this).attr('r', 4);
          tooltip.style('opacity', 0);
        });

    // X Axis
    const tickCount = Math.floor(innerWidth / 60);
    const everyNth = Math.ceil(displayData.length / tickCount);

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(x)
          .tickValues(displayData.map((_, i) => i).filter((_, i) => i % everyNth === 0))
          .tickFormat((d) => displayData[d as number].label)
          .tickSize(0)
      )
      .call(g => g.select('.domain').attr('stroke', '#e5e7eb'))
      .call(g => g.selectAll('text')
        .attr('fill', '#6b7280')
        .attr('dy', '1em')
        .style('font-size', '11px')
      );

    // Y Axis
    g.append('g')
      .call(d3.axisLeft(y).ticks(5))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('text')
        .attr('fill', '#6b7280')
        .style('font-size', '12px')
      )
      .call(g => g.selectAll('.tick line').remove());

    // Y Axis Label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerHeight / 2)
      .attr('y', -35)
      .attr('fill', '#6b7280')
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', '500')
      .text('Hours');

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
