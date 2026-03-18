<script lang="ts">
  export let meals: {
    timestamp: string;
    meal_name: string;
    meal_type: string;
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
  }[] = [];
  export let maxDays: number = 7;

  // Group meals by date
  $: groupedMeals = meals.reduce((acc, meal) => {
    const date = new Date(meal.timestamp);
    const dateKey = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    if (!acc[dateKey]) {
      acc[dateKey] = [];
    }
    acc[dateKey].push(meal);
    return acc;
  }, {} as Record<string, typeof meals>);

  $: sortedDates = Object.keys(groupedMeals).reverse().slice(0, maxDays);

  function formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }

  function getMealTypeEmoji(type: string): string {
    const emojiMap: Record<string, string> = {
      breakfast: '🌅',
      lunch: '☀️',
      dinner: '🌙',
      snack: '🍎',
      unspecified: '🍽️'
    };
    return emojiMap[type] || '🍽️';
  }

  function getMealTypeColor(type: string): string {
    const colorMap: Record<string, string> = {
      breakfast: '#f59e0b',
      lunch: '#10b981',
      dinner: '#6366f1',
      snack: '#8b5cf6',
      unspecified: '#6b7280'
    };
    return colorMap[type] || '#6b7280';
  }
</script>

<div class="meals-timeline">
  {#if sortedDates.length === 0}
    <div class="empty-state">
      <p>No meal data tracked yet</p>
    </div>
  {:else}
    {#each sortedDates as date}
      <div class="day-section">
        <div class="day-header">
          <h3>{date}</h3>
          <div class="day-summary">
            {groupedMeals[date].length} {groupedMeals[date].length === 1 ? 'item' : 'items'}
            • {Math.round(groupedMeals[date].reduce((sum, m) => sum + m.calories, 0))} cal
          </div>
        </div>

        <div class="meals-list">
          {#each groupedMeals[date] as meal}
            <div class="meal-item">
              <div class="meal-time-type">
                <span class="meal-emoji">{getMealTypeEmoji(meal.meal_type)}</span>
                <span class="meal-time">{formatTime(meal.timestamp)}</span>
              </div>

              <div class="meal-details">
                <div class="meal-name">{meal.meal_name}</div>

                <div class="meal-macros">
                  <span class="macro calories">{Math.round(meal.calories)} cal</span>
                  <span class="macro-separator">•</span>
                  <span class="macro protein">P: {meal.protein_g.toFixed(0)}g</span>
                  <span class="macro-separator">•</span>
                  <span class="macro carbs">C: {meal.carbs_g.toFixed(0)}g</span>
                  <span class="macro-separator">•</span>
                  <span class="macro fat">F: {meal.fat_g.toFixed(0)}g</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  .meals-timeline {
    height: 100%;
    overflow-y: auto;
    padding: 0.5rem;
    font-family: 'Georgia', 'Times New Roman', serif;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #9ca3af;
    font-style: italic;
  }

  .day-section {
    margin-bottom: 1.5rem;
  }

  .day-section:last-child {
    margin-bottom: 0;
  }

  .day-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e7e5e4;
    margin-bottom: 0.75rem;
  }

  .day-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 500;
    color: #1c1917;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .day-summary {
    font-size: 0.75rem;
    color: #78716c;
    font-weight: 400;
  }

  .meals-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .meal-item {
    display: flex;
    gap: 0.75rem;
    padding: 0.625rem 0.75rem;
    background: #f5f5f4;
    border: 1px solid #e7e5e4;
    border-radius: 2px;
    transition: background 0.15s ease;
  }

  .meal-item:hover {
    background: #e7e5e4;
  }

  .meal-time-type {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    min-width: 45px;
    padding-top: 0.125rem;
  }

  .meal-emoji {
    font-size: 1.25rem;
    line-height: 1;
  }

  .meal-time {
    font-size: 0.625rem;
    color: #78716c;
    font-weight: 400;
    white-space: nowrap;
  }

  .meal-details {
    flex: 1;
    min-width: 0;
  }

  .meal-name {
    font-size: 0.8125rem;
    font-weight: 500;
    color: #1c1917;
    margin-bottom: 0.375rem;
    line-height: 1.3;
  }

  .meal-macros {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
    font-size: 0.6875rem;
    color: #57534e;
  }

  .macro {
    font-weight: 400;
  }

  .macro.calories {
    font-weight: 500;
    color: #1c1917;
  }

  .macro-separator {
    color: #d6d3d1;
  }

  /* Custom scrollbar for timeline */
  .meals-timeline::-webkit-scrollbar {
    width: 8px;
  }

  .meals-timeline::-webkit-scrollbar-track {
    background: #f5f5f4;
    border-radius: 4px;
  }

  .meals-timeline::-webkit-scrollbar-thumb {
    background: #d6d3d1;
    border-radius: 4px;
  }

  .meals-timeline::-webkit-scrollbar-thumb:hover {
    background: #a8a29e;
  }
</style>
