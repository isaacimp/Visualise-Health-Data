<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: { label: string; value: number }[] = [];
  export let color: string = '#4CAF50';
  export let maxPoints: number = 30;
  export let targetCalories: number = 2000;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 30, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleBand()
      .domain(displayData.map(d => d.label))
      .range([0, innerWidth])
      .padding(0.2);

    const maxDataValue = d3.max(displayData, d => d.value) || 0;
    const maxValue = Math.max(targetCalories + 500, maxDataValue + 200);

    const y = d3.scaleLinear()
      .domain([0, maxValue])
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

    // Bars
    g.selectAll('.bar')
      .data(displayData)
      .join('rect')
        .attr('class', 'bar')
        .attr('x', d => x(d.label)!)
        .attr('y', d => y(d.value))
        .attr('width', x.bandwidth())
        .attr('height', d => innerHeight - y(d.value))
        .attr('fill', d => {
          // Clean, professional colors
          if (d.value === 0) return '#e5e7eb';  // Light gray for missing data
          if (d.value > targetCalories + 300) return '#dc2626';  // Clean red for over
          if (d.value < targetCalories - 300) return '#f59e0b';  // Amber for under
          return '#0d9488';  // Clean teal for on target
        })
        .attr('opacity', d => d.value === 0 ? 0.3 : 0.85)
        .attr('rx', 2)
        .on('mouseover', function(event, d) {
          if (d.value === 0) return;
          d3.select(this).attr('opacity', 1);
          tooltip
            .style('opacity', 1)
            .html(`<strong>${d.label}</strong><br/>${Math.round(d.value).toLocaleString()} cal`)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 28}px`);
        })
        .on('mouseout', function(event, d) {
          d3.select(this).attr('opacity', d.value === 0 ? 0.3 : 0.85);
          tooltip.style('opacity', 0);
        });

    // X Axis
    const tickCount = Math.floor(innerWidth / 60);
    const everyNth = Math.ceil(displayData.length / tickCount);

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(x)
          .tickValues(displayData.filter((_, i) => i % everyNth === 0).map(d => d.label))
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
      .call(d3.axisLeft(y).ticks(6))
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
      .attr('y', -45)
      .attr('fill', '#6b7280')
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', '500')
      .text('Calories');

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
