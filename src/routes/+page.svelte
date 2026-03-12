<script lang="ts">
  import LineChart from '$lib/charts/LineChart.svelte';
  import ChartCard from '$lib/components/ChartCard.svelte';
  import BarChart from '$lib/charts/BarChart.svelte';
  import Heatmap from '$lib/charts/Heatmap.svelte';

  const sales = [
    { label: 'Jan', value: 420 },
    { label: 'Feb', value: 380 },
    { label: 'Mar', value: 510 },
    { label: 'Apr', value: 390 },
    { label: 'May', value: 620 },
    { label: 'Jun', value: 550 },
    { label: 'Jul', value: 420 },
    { label: 'Aug', value: 380 },
    { label: 'Sep', value: 510 },
    { label: 'Oct', value: 390 },
    { label: 'Nov', value: 620 },
    { label: 'Dec', value: 550 },
    { label: 'Jan', value: 420 },
    { label: 'Feb', value: 380 },
    { label: 'Mar', value: 510 },
    { label: 'Apr', value: 390 },
    { label: 'May', value: 620 },
    { label: 'Jun', value: 550 },
  ];
  const data = [
    { label: 'Jan', value: 10 },
    { label: 'Feb', value: 40 },
    { label: 'Mar', value: 25 },
    { label: 'Apr', value: 60 },
    { label: 'May', value: 35 },
    { label: 'Jun', value: 80 },
    { label: 'Jul', value: 55 },
    { label: 'Aug', value: 10 },
    { label: 'Sep', value: 40 },
    { label: 'Oct', value: 25 },
    { label: 'Nov', value: 60 },
    { label: 'Dec', value: 35 },
  ];

  // Heatmap data: days of week vs hours of day
  const heatmapData = (() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const hours = ['Morning', 'Afternoon', 'Evening', 'Night'];
    const result = [];
    for (const day of days) {
      for (const hour of hours) {
        result.push({
          group: day,
          variable: hour,
          value: Math.floor(Math.random() * 90) + 10
        });
      }
    }
    return result;
  })();

</script>

<div class="title">
  <h1>Quantified Self Dashboard</h1>
</div>
<div class="dashboard">
  <ChartCard title="Revenue Over Time">
    <LineChart data={data} />
  </ChartCard>
  <ChartCard title="Monthly Sales">
    <BarChart data={sales} color="#6366f1" />
  </ChartCard>
  <ChartCard title="Activity Heatmap">
    <Heatmap data={heatmapData} />
  </ChartCard>
</div>

<style>
  .dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
    gap: 1.5rem;
    padding: 2rem;
    align-items: start;
    font-size: x-small;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  }
  .title {
    color: black;
    font-family:system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    text-align: center;
  }
</style>