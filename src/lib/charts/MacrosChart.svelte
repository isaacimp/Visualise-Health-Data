<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import * as d3 from 'd3';

  export let data: {
    label: string;
    protein: number;
    carbs: number;
    fat: number;
  }[] = [];
  export let maxPoints: number = 30;

  let svgEl: SVGSVGElement;
  let container: HTMLDivElement;
  let observer: ResizeObserver;

  $: displayData = data.slice(-maxPoints);

  // Macro colors - Clean, distinct palette
  const macroColors = {
    protein: '#dc2626',  // Clean red
    carbs: '#0d9488',    // Clean teal
    fat: '#f59e0b'       // Amber
  };

  function draw() {
    if (!container || !svgEl || displayData.length === 0) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 30, right: 100, bottom: 40, left: 60 };
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
      .keys(['protein', 'carbs', 'fat'])
      .value((d: any, key) => d[key] || 0);

    const series = stack(displayData as any);

    // Scales
    const x = d3.scaleLinear()
      .domain([0, displayData.length - 1])
      .range([0, innerWidth]);

    const maxTotal = d3.max(displayData, d => d.protein + d.carbs + d.fat) || 100;
    const y = d3.scaleLinear()
      .domain([0, maxTotal * 1.1])
      .nice()
      .range([innerHeight, 0]);

    const colorMap: { [key: string]: string } = {
      'protein': macroColors.protein,
      'carbs': macroColors.carbs,
      'fat': macroColors.fat
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

    // Area generator
    const area = d3.area<any>()
      .x((d, i) => x(i))
      .y0(d => y(d[0]))
      .y1(d => y(d[1]))
      .curve(d3.curveCatmullRom);

    // Draw stacked areas
    g.append('g')
      .selectAll('path')
      .data(series)
      .join('path')
        .attr('fill', d => colorMap[d.key])
        .attr('opacity', 0.7)
        .attr('d', area)
        .on('mouseover', function() {
          d3.select(this).attr('opacity', 0.9);
        })
        .on('mouseout', function() {
          d3.select(this).attr('opacity', 0.7);
        });

    // Interactive overlay for tooltips
    const bisect = d3.bisector((d: any, x: number) => x).left;

    const focus = g.append('g')
      .style('display', 'none');

    focus.append('line')
      .attr('class', 'focus-line')
      .attr('stroke', '#6b7280')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3');

    g.append('rect')
      .attr('class', 'overlay')
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .style('fill', 'none')
      .style('pointer-events', 'all')
      .on('mouseover', () => {
        focus.style('display', null);
        tooltip.style('opacity', 1);
      })
      .on('mouseout', () => {
        focus.style('display', 'none');
        tooltip.style('opacity', 0);
      })
      .on('mousemove', function(event) {
        const [mouseX] = d3.pointer(event);
        const xIndex = Math.round(x.invert(mouseX));
        const validIndex = Math.max(0, Math.min(displayData.length - 1, xIndex));
        const d = displayData[validIndex];

        focus.select('.focus-line')
          .attr('x1', x(validIndex))
          .attr('x2', x(validIndex))
          .attr('y1', 0)
          .attr('y2', innerHeight);

        const total = d.protein + d.carbs + d.fat;
        tooltip
          .html(`
            <strong>${d.label}</strong><br/>
            <div style="margin-top: 6px;">
              <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: ${macroColors.protein}; border-radius: 2px;"></span>
                <span>Protein: ${d.protein.toFixed(1)}g</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: ${macroColors.carbs}; border-radius: 2px;"></span>
                <span>Carbs: ${d.carbs.toFixed(1)}g</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: ${macroColors.fat}; border-radius: 2px;"></span>
                <span>Fat: ${d.fat.toFixed(1)}g</span>
              </div>
              <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #e5e7eb; font-weight: 500;">
                Total: ${total.toFixed(1)}g
              </div>
            </div>
          `)
          .style('left', `${event.offsetX + 10}px`)
          .style('top', `${event.offsetY - 28}px`);
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
      .text('Grams');

    // Legend
    const legend = svg.append('g')
      .attr('transform', `translate(${width - margin.right + 15},${margin.top})`);

    const legendData = [
      { label: 'Protein', color: macroColors.protein },
      { label: 'Carbs', color: macroColors.carbs },
      { label: 'Fat', color: macroColors.fat }
    ];

    legendData.forEach((item, i) => {
      const legendRow = legend.append('g')
        .attr('transform', `translate(0,${i * 24})`);

      legendRow.append('rect')
        .attr('width', 14)
        .attr('height', 14)
        .attr('fill', item.color)
        .attr('opacity', 0.7)
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
