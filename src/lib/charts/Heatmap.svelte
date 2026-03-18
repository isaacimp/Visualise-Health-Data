<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: { group: string; variable: string; value: number }[] = [];

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  function draw() {
    if (!container || !svgEl || !data.length) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 10, right: 25, bottom: 30, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Labels of row and columns
    const myGroups = Array.from(new Set(data.map(d => d.group)));
    const myVars = Array.from(new Set(data.map(d => d.variable)));

    // Build X scales and axis
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(myGroups)
      .padding(0.05);

    g.append('g')
      .style('font-size', 12)
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).tickSize(0))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('text').attr('fill', '#888'));

    // Build Y scales and axis
    const y = d3.scaleBand()
      .range([innerHeight, 0])
      .domain(myVars)
      .padding(0.05);

    g.append('g')
      .style('font-size', 12)
      .call(d3.axisLeft(y).tickSize(0))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('text').attr('fill', '#888'));

    // Build color scale - Professional blue-gray gradient
    const myColor = d3.scaleSequential()
      .interpolator(d3.interpolatePuBu)  // Professional blues
      .domain([1, d3.max(data, d => d.value) || 100]);

    // Create tooltip
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

    // Tooltip interaction functions
    const mouseover = function(this: any) {
      tooltip.style('opacity', 1);
      d3.select(this)
        .style('stroke', 'white')
        .style('opacity', 1);
    };

    const mousemove = function(this: any, event: any, d: any) {
      tooltip
        .html(`<strong>${d.group} - ${d.variable}</strong><br/>Value: ${d.value}`)
        .style('left', `${event.offsetX + 10}px`)
        .style('top', `${event.offsetY - 28}px`);
    };

    const mouseleave = function(this: any) {
      tooltip.style('opacity', 0);
      d3.select(this)
        .style('stroke', 'none')
        .style('opacity', 0.8);
    };

    // Add the squares
    g.selectAll('rect')
      .data(data, (d: any) => `${d.group}:${d.variable}`)
      .join('rect')
      .attr('x', (d: any) => x(d.group) || 0)
      .attr('y', (d: any) => y(d.variable) || 0)
      .attr('rx', 4)
      .attr('ry', 4)
      .attr('width', x.bandwidth())
      .attr('height', y.bandwidth())
      .style('fill', (d: any) => myColor(d.value))
      .style('stroke-width', 4)
      .style('stroke', 'none')
      .style('opacity', 0.8)
      .on('mouseover', mouseover)
      .on('mousemove', mousemove)
      .on('mouseleave', mouseleave);

    // Add title
    svg.append('text')
      .attr('x', margin.left)
      .attr('y', 25)
      .attr('text-anchor', 'left')
      .style('font-size', '18px')
      .style('fill', '#fff');
  }

  onMount(() => {
    observer = new ResizeObserver(() => draw());
    observer.observe(container);
    draw();
  });

  onDestroy(() => {
    observer?.disconnect();
  });

  $: if (data) draw();
</script>

<div bind:this={container} style="position: relative; width: 100%; height: 100%;">
  <svg bind:this={svgEl} style="display: block;" />
</div>
