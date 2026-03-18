<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import LineChart from '$lib/charts/LineChart.svelte';
  import ChartCard from '$lib/components/ChartCard.svelte';
  import BarChart from '$lib/charts/BarChart.svelte';
  import StackedBarChart from '$lib/charts/StackedBarChart.svelte';
  import SleepDurationChart from '$lib/charts/SleepDurationChart.svelte';
  import SleepStagesChart from '$lib/charts/SleepStagesChart.svelte';
  import ChartControls from '$lib/components/ChartControls.svelte';
  import CaloriesChart from '$lib/charts/CaloriesChart.svelte';
  import MacrosChart from '$lib/charts/MacrosChart.svelte';
  import MealsTimeline from '$lib/charts/MealsTimeline.svelte';

  // Types
  interface StepsData {
    date: string;
    steps: number;
  }

  interface SleepData {
    date: string;
    duration_hours: number;
    light_sleep: number;
    deep_sleep: number;
    rem_sleep: number;
    awake_minutes: number;
    start_datetime: string;
    end_datetime: string;
  }

  interface HeartRateData {
    date: string;
    avg_bpm: number;
    min_bpm: number;
    max_bpm: number;
  }

  interface WeightData {
    date: string;
    weight_kg: number;
    weight_lbs: number;
  }

  interface DailyNutritionData {
    date: string;
    total_calories: number;
    total_protein: number;
    total_carbs: number;
    total_fat: number;
    total_fiber: number;
    meal_count: number;
  }

  interface NutritionMeal {
    timestamp: string;
    meal_name: string;
    meal_type: string;
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g: number;
    sugar_g: number;
  }

  // Data stores
  let stepsData: { label: string; value: number }[] = [];
  let sleepDurationData: { label: string; value: number }[] = [];
  let sleepStagesData: {
    label: string;
    light: number;
    deep: number;
    rem: number;
    awake: number;
  }[] = [];
  let heartRateData: { label: string; value: number }[] = [];
  let weightData: { label: string; value: number }[] = [];
  let caloriesData: { label: string; value: number }[] = [];
  let macrosData: { label: string; protein: number; carbs: number; fat: number }[] = [];
  let mealsData: NutritionMeal[] = [];

  // Time range controls - independent for each chart
  let stepsDays = 9999;
  let sleepDurationDays = 9999;
  let sleepStagesDays = 9999;
  let heartDays = 9999;
  let weightDays = 9999;
  let caloriesDays = 9999;
  let macrosDays = 9999;
  let mealsDays = 7;  // Default to 7 days for meal detail view

  let loading = true;
  let error = '';
  let initialLoad = true;
  let syncing = false;
  let syncMessage = '';

  // Format date for display (MM/DD)
  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  }

  // Load data function
  async function loadData() {
    try {
      // Don't show loading spinner on filter changes to prevent scroll jump
      // if (!initialLoad) loading = true;

      // Fetch steps data
      const steps: StepsData[] = await invoke('get_steps_data', { days: stepsDays });
      stepsData = steps
        .reverse()
        .map(s => ({
          label: formatDate(s.date),
          value: s.steps
        }));

      // Fetch sleep data (using max of both sleep chart ranges)
      const sleepDaysMax = Math.max(sleepDurationDays, sleepStagesDays);
      const sleep: SleepData[] = await invoke('get_sleep_data', { days: sleepDaysMax });

      // Process sleep duration data
      sleepDurationData = sleep
        .reverse()
        .map(s => ({
          label: formatDate(s.date),
          value: s.duration_hours
        }));

      // Process sleep stages data
      sleepStagesData = sleep
        .reverse()
        .map(s => ({
          label: formatDate(s.date),
          light: s.light_sleep,
          deep: s.deep_sleep,
          rem: s.rem_sleep,
          awake: s.awake_minutes
        }));

      // Fetch heart rate data
      const heartRate: HeartRateData[] = await invoke('get_heart_rate_data', { days: heartDays });
      heartRateData = heartRate
        .reverse()
        .map(h => ({
          label: formatDate(h.date),
          value: Math.round(h.avg_bpm)
        }));

      // Fetch weight data
      const weight: WeightData[] = await invoke('get_weight_data', { days: weightDays });
      weightData = weight
        .reverse()
        .map(w => ({
          label: formatDate(w.date),
          value: w.weight_kg
        }));

      // Fetch nutrition data (using max of calories and macros ranges)
      const nutritionDaysMax = Math.max(caloriesDays, macrosDays);
      const nutrition: DailyNutritionData[] = await invoke('get_daily_nutrition_data', { days: nutritionDaysMax });

      // Process calories data
      caloriesData = nutrition
        .reverse()
        .map(n => ({
          label: formatDate(n.date),
          value: n.total_calories
        }));

      // Process macros data
      macrosData = nutrition
        .reverse()
        .map(n => ({
          label: formatDate(n.date),
          protein: n.total_protein,
          carbs: n.total_carbs,
          fat: n.total_fat
        }));

      // Fetch individual meals
      const meals: NutritionMeal[] = await invoke('get_nutrition_meals', { days: mealsDays });
      mealsData = meals;

      loading = false;
      initialLoad = false;
    } catch (err) {
      console.error('Error loading health data:', err);
      error = String(err);
      loading = false;
      initialLoad = false;
    }
  }

  // Sync function to update data from Google Drive
  async function syncData() {
    syncing = true;
    syncMessage = 'Syncing...';
    try {
      await invoke('sync_health_data');
      syncMessage = 'Sync complete! Reloading data...';
      await loadData();
      syncMessage = 'Data updated successfully!';
      setTimeout(() => { syncMessage = ''; }, 3000);
    } catch (err) {
      console.error('Sync error:', err);
      syncMessage = `Sync failed: ${err}`;
      setTimeout(() => { syncMessage = ''; }, 5000);
    } finally {
      syncing = false;
    }
  }

  // Load data on mount
  onMount(() => {
    loadData();
  });

  // Reload data when time ranges change
  $: if (!initialLoad && (stepsDays || sleepDurationDays || sleepStagesDays || heartDays || weightDays || caloriesDays || macrosDays || mealsDays)) {
    loadData();
  }

</script>

<div class="title">
  <div class="title-content">
    <div>
      <h1>Health Dashboard</h1>
      <p class="subtitle">Quanified health. Current data sources: Garmin, Renpho, Cronometer</p>
    </div>
    <div class="sync-controls">
      <button class="sync-btn" on:click={syncData} disabled={syncing}>
        {syncing ? 'Syncing...' : 'Sync Data'}
      </button>
      {#if syncMessage}
        <p class="sync-message">{syncMessage}</p>
      {/if}
    </div>
  </div>
</div>

{#if loading}
  <div class="loading">
    <p>Loading your health data...</p>
  </div>
{:else if error}
  <div class="error">
    <p>Error loading data: {error}</p>
    <p class="hint">Make sure you've run the import script to sync your Health Connect data.</p>
  </div>
{:else}
  <div class="dashboard">
    <ChartCard title="Daily Steps">
      <ChartControls bind:selectedDays={stepsDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 365, label: '1y' },
        { value: 9999, label: 'All' }
      ]} />
      <BarChart data={stepsData} color="#0d9488" maxPoints={stepsDays} />
    </ChartCard>

    <ChartCard title="Sleep Duration">
      <ChartControls bind:selectedDays={sleepDurationDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 9999, label: 'All' }
      ]} />
      <SleepDurationChart data={sleepDurationData} color="#7c3aed" maxPoints={sleepDurationDays} targetHours={8} />
    </ChartCard>

    <ChartCard title="Sleep Stages">
      <ChartControls bind:selectedDays={sleepStagesDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 9999, label: 'All' }
      ]} />
      <SleepStagesChart data={sleepStagesData} maxPoints={sleepStagesDays} />
    </ChartCard>

    <ChartCard title="Heart Rate">
      <ChartControls bind:selectedDays={heartDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 9999, label: 'All' }
      ]} />
      <LineChart data={heartRateData} color="#dc2626" maxPoints={heartDays} />
    </ChartCard>

    <ChartCard title="Body Weight">
      <ChartControls bind:selectedDays={weightDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 365, label: '1y' },
        { value: 9999, label: 'All' }
      ]} />
      <LineChart data={weightData} color="#f59e0b" maxPoints={weightDays} />
    </ChartCard>

    <ChartCard title="Daily Calories">
      <ChartControls bind:selectedDays={caloriesDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 9999, label: 'All' }
      ]} />
      <CaloriesChart data={caloriesData} color="#0d9488" maxPoints={caloriesDays} targetCalories={2000} />
    </ChartCard>

    <ChartCard title="Macronutrients">
      <ChartControls bind:selectedDays={macrosDays} options={[
        { value: 7, label: '7d' },
        { value: 30, label: '30d' },
        { value: 90, label: '90d' },
        { value: 9999, label: 'All' }
      ]} />
      <MacrosChart data={macrosData} maxPoints={macrosDays} />
    </ChartCard>

    <ChartCard title="Meal Log" height="400px">
      <ChartControls bind:selectedDays={mealsDays} options={[
        { value: 3, label: '3d' },
        { value: 7, label: '7d' },
        { value: 14, label: '14d' },
        { value: 30, label: '30d' }
      ]} />
      <MealsTimeline meals={mealsData} maxDays={mealsDays} />
    </ChartCard>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Total Days</div>
      <div class="stat-value">{stepsData.length}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Steps/Day</div>
      <div class="stat-value">
        {Math.round(stepsData.reduce((sum, d) => sum + d.value, 0) / stepsData.length).toLocaleString()}
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Sleep</div>
      <div class="stat-value">
        {sleepDurationData.length > 0 ? (sleepDurationData.reduce((sum, d) => sum + d.value, 0) / sleepDurationData.length).toFixed(1) : '-'}h
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Heart Rate</div>
      <div class="stat-value">
        {Math.round(heartRateData.reduce((sum, d) => sum + d.value, 0) / heartRateData.length)} BPM
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Current Weight</div>
      <div class="stat-value">
        {weightData.length > 0 ? weightData[weightData.length - 1].value.toFixed(1) : '-'} kg
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Calories/Day</div>
      <div class="stat-value">
        {caloriesData.filter(d => d.value > 0).length > 0 ? Math.round(caloriesData.filter(d => d.value > 0).reduce((sum, d) => sum + d.value, 0) / caloriesData.filter(d => d.value > 0).length) : '-'}
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Days Tracked</div>
      <div class="stat-value">
        {caloriesData.filter(d => d.value > 0).length}
      </div>
    </div>
  </div>
{/if}

<style>
  :global(body) {
    background: #fafaf9;
  }

  .title {
    color: #1c1917;
    font-family: 'Georgia', 'Times New Roman', serif;
    padding: 2rem 2rem 1rem;
    border-bottom: 2px solid #292524;
    margin-bottom: 2rem;
  }

  .title-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1400px;
    margin: 0 auto;
  }

  .title h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
    font-weight: 400;
    letter-spacing: 0.02em;
  }

  .subtitle {
    color: #57534e;
    font-size: 0.875rem;
    margin: 0;
    font-style: italic;
    font-weight: 300;
  }

  .sync-controls {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .sync-btn {
    padding: 0.5rem 1rem;
    background: #374151;
    color: white;
    border: 1px solid #374151;
    border-radius: 2px;
    font-size: 0.875rem;
    font-weight: 500;
    font-family: 'Georgia', 'Times New Roman', serif;
    cursor: pointer;
    transition: all 0.15s ease;
    letter-spacing: 0.01em;
  }

  .sync-btn:hover:not(:disabled) {
    background: #1f2937;
    border-color: #1f2937;
  }

  .sync-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .sync-message {
    font-size: 0.75rem;
    color: #57534e;
    margin: 0;
    font-style: italic;
  }

  .dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
    gap: 1.5rem;
    padding: 0 2rem 2rem;
    align-items: start;
    font-family: 'Georgia', 'Times New Roman', serif;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    padding: 0 2rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
    border-top: 1px solid #d6d3d1;
    padding-top: 2rem;
  }

  .stat-card {
    background: #fefdfb;
    border: 1px solid #d6d3d1;
    border-radius: 2px;
    padding: 1.25rem;
    text-align: center;
  }

  .stat-label {
    color: #57534e;
    font-size: 0.75rem;
    font-weight: 400;
    margin-bottom: 0.5rem;
    font-family: 'Georgia', 'Times New Roman', serif;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-value {
    color: #1c1917;
    font-size: 1.75rem;
    font-weight: 400;
    font-family: 'Georgia', 'Times New Roman', serif;
  }

  .loading,
  .error {
    text-align: center;
    padding: 4rem 2rem;
    font-family: 'Georgia', 'Times New Roman', serif;
  }

  .error {
    color: #991b1b;
  }

  .hint {
    color: #6b7280;
    font-size: 0.875rem;
    margin-top: 0.5rem;
  }

  .loading p {
    color: #6b7280;
    font-size: 1.125rem;
  }
</style>
