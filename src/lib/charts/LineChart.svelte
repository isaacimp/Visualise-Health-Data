<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as d3 from 'd3';

  export let data: { label: string; value: number }[] = [];
  export let color: string = '#6366f1';
  export let maxPoints: number = 50;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scalePoint()
      .domain(displayData.map(d => d.label))
      .range([0, innerWidth]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(displayData, d => d.value)!])
      .nice()
      .range([innerHeight, 0]);

    // Gridlines
    g.append('g')
      .call(d3.axisLeft(y).tickSize(-innerWidth).tickFormat(() => ''))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('.tick line')
        .attr('stroke', '#2a2a4a')
        .attr('stroke-dasharray', '3,3')
      );

    // Area fill under line
    const area = d3.area<{ label: string; value: number }>()
      .x(d => x(d.label)!)
      .y0(innerHeight)
      .y1(d => y(d.value))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(displayData)
      .attr('fill', color)
      .attr('fill-opacity', 0.1)
      .attr('d', area);

    // Line
    const line = d3.line<{ label: string; value: number }>()
      .x(d => x(d.label)!)
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(displayData)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2)
      .attr('d', line);

    // Dots
    g.selectAll('circle')
      .data(displayData)
      .join('circle')
      .attr('cx', d => x(d.label)!)
      .attr('cy', d => y(d.value))
      .attr('r', Math.max(2, 5 - displayData.length / 15)) // shrink dots when many points
      .attr('fill', color)
      .on('mouseover', function (event, d) {
        d3.select(this).attr('r', 6).attr('fill', color);
        tooltip
          .style('opacity', 1)
          .html(`<strong>${d.label}</strong><br/>${d.value}`)
          .style('left', `${event.offsetX + 10}px`)
          .style('top', `${event.offsetY - 28}px`);
      })
      .on('mouseout', function (_, d) {
        d3.select(this)
          .attr('r', Math.max(2, 5 - displayData.length / 15))
          .attr('fill', color);
        tooltip.style('opacity', 0);
      });

    // X Axis
    const tickCount = Math.floor(innerWidth / 60); // one tick per ~60px
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
        .style('font-size', '11px')
      );

    // Y Axis
    g.append('g')
      .call(d3.axisLeft(y).ticks(5))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('text').attr('fill', '#888'))
      .call(g => g.selectAll('.tick line').remove());

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

  onDestroy(() => observer?.disconnect());

  $: if (displayData) draw();
</script>

<div bind:this={container} style="position: relative; width: 100%; height: 100%;">
  <svg bind:this={svgEl} style="display: block;" />
</div>