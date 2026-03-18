<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: { label: string; value: number; quality: string; efficiency: number }[] = [];
  export let maxPoints: number = 30;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 40, right: 20, bottom: 40, left: 40 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Radial layout for quality visualization
    const radius = Math.min(innerWidth, innerHeight) / 2;
    const centerX = innerWidth / 2;
    const centerY = innerHeight / 2;

    const angleScale = d3.scaleBand()
      .domain(displayData.map((_, i) => i.toString()))
      .range([0, 2 * Math.PI])
      .padding(0.1);

    const radiusScale = d3.scaleLinear()
      .domain([0, 100])
      .range([0, radius * 0.8]);

    const colorScale = d3.scaleSequential()
      .domain([0, 100])
      .interpolator(d3.interpolateRgbBasis(['#dc2626', '#f59e0b', '#10b981', '#6366f1']));

    // Draw arcs for each day
    const arc = d3.arc();

    displayData.forEach((d, i) => {
      const startAngle = angleScale(i.toString())!;
      const endAngle = startAngle + angleScale.bandwidth();
      const innerRadius = 0;
      const outerRadius = radiusScale(d.value);

      // Quality arc
      g.append('path')
        .attr('transform', `translate(${centerX},${centerY})`)
        .attr('d', arc({
          innerRadius,
          outerRadius,
          startAngle,
          endAngle
        } as any))
        .attr('fill', colorScale(d.value))
        .attr('opacity', 0.8)
        .on('mouseover', function(event) {
          d3.select(this).attr('opacity', 1);
          tooltip
            .style('opacity', 1)
            .html(`
              <strong>${d.label}</strong><br/>
              Quality: ${d.value.toFixed(1)}% (${d.quality})<br/>
              Efficiency: ${d.efficiency.toFixed(1)}%
            `)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 28}px`);
        })
        .on('mouseout', function() {
          d3.select(this).attr('opacity', 0.8);
          tooltip.style('opacity', 0);
        });

      // Efficiency ring (outer)
      const efficiencyInner = radiusScale(d.value);
      const efficiencyOuter = efficiencyInner + 5;

      g.append('path')
        .attr('transform', `translate(${centerX},${centerY})`)
        .attr('d', arc({
          innerRadius: efficiencyInner,
          outerRadius: efficiencyOuter,
          startAngle,
          endAngle
        } as any))
        .attr('fill', d.efficiency >= 95 ? '#10b981' : d.efficiency >= 90 ? '#f59e0b' : '#dc2626')
        .attr('opacity', 0.6);
    });

    // Center circle
    g.append('circle')
      .attr('cx', centerX)
      .attr('cy', centerY)
      .attr('r', 3)
      .attr('fill', '#888');

    // Legend
    const legend = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top - 30})`);

    const legendData = [
      { label: 'Excellent (>50%)', color: colorScale(75) },
      { label: 'Good (40-50%)', color: colorScale(45) },
      { label: 'Fair (30-40%)', color: colorScale(35) },
      { label: 'Poor (<30%)', color: colorScale(20) }
    ];

    legendData.forEach((item, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(${i * 120},0)`);

      legendItem.append('rect')
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', item.color)
        .attr('rx', 2);

      legendItem.append('text')
        .attr('x', 18)
        .attr('y', 10)
        .attr('fill', '#888')
        .style('font-size', '10px')
        .text(item.label);
    });

    // Tooltip
    d3.select(container).selectAll('.tooltip').remove();
    const tooltip = d3.select(container)
      .append('div')
      .attr('class', 'tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', '#1a1a2e')
      .style('border', '1px solid #2a2a4a')
      .style('border-radius', '6px')
      .style('padding', '8px 12px')
      .style('font-size', '13px')
      .style('color', '#fff')
      .style('pointer-events', 'none');
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
