<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: { label: string; values: { [key: string]: number } }[] = [];
  export let colors: { [key: string]: string } = {};
  export let maxPoints: number = 30;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);
  $: keys = displayData.length > 0 ? Object.keys(displayData[0].values) : [];

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 100, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Stack the data
    const stack = d3.stack()
      .keys(keys)
      .value((d: any, key) => d.values[key] || 0);

    const series = stack(displayData as any);

    // Scales
    const x = d3.scaleBand()
      .domain(displayData.map(d => d.label))
      .range([0, innerWidth])
      .padding(0.3);

    const y = d3.scaleLinear()
      .domain([0, d3.max(series, d => d3.max(d, d => d[1]))!])
      .nice()
      .range([innerHeight, 0]);

    const color = d3.scaleOrdinal()
      .domain(keys)
      .range(keys.map(k => colors[k] || '#6366f1'));

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
        .attr('stroke', '#2a2a4a')
        .attr('stroke-dasharray', '3,3')
      );

    // Bars
    g.append('g')
      .selectAll('g')
      .data(series)
      .join('g')
        .attr('fill', d => color(d.key) as string)
      .selectAll('rect')
      .data(d => d)
      .join('rect')
        .attr('x', (d: any) => x(d.data.label)!)
        .attr('y', d => y(d[1]))
        .attr('height', d => y(d[0]) - y(d[1]))
        .attr('width', x.bandwidth())
        .attr('rx', 2)
        .on('mouseover', function (event, d: any) {
          const key = d3.select(this.parentNode).datum() as any;
          const value = d.data.values[key.key];
          d3.select(this).attr('opacity', 0.8);
          tooltip
            .style('opacity', 1)
            .html(`<strong>${d.data.label}</strong><br/>${key.key}: ${value.toFixed(1)}`)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 28}px`);
        })
        .on('mouseout', function () {
          d3.select(this).attr('opacity', 1);
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
      .call(g => g.select('.domain').attr('stroke', '#2a2a4a'))
      .call(g => g.selectAll('text')
        .attr('fill', '#888')
        .attr('dy', '1.5em')
        .style('font-size', '10px')
        .attr('transform', 'rotate(-45)')
        .style('text-anchor', 'end')
      );

    // Y Axis
    g.append('g')
      .call(d3.axisLeft(y).ticks(5))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('text').attr('fill', '#888'))
      .call(g => g.selectAll('.tick line').remove());

    // Legend
    const legend = svg.append('g')
      .attr('transform', `translate(${width - margin.right + 10},${margin.top})`);

    keys.forEach((key, i) => {
      const legendRow = legend.append('g')
        .attr('transform', `translate(0,${i * 20})`);

      legendRow.append('rect')
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', color(key) as string)
        .attr('rx', 2);

      legendRow.append('text')
        .attr('x', 18)
        .attr('y', 10)
        .attr('fill', '#888')
        .style('font-size', '11px')
        .text(key);
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
