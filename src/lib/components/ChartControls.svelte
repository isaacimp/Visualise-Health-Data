<script lang="ts">
  export let selectedDays: number;
  export let options: { value: number; label: string }[] = [
    { value: 7, label: '7 days' },
    { value: 14, label: '14 days' },
    { value: 30, label: '30 days' },
    { value: 60, label: '60 days' },
    { value: 90, label: '90 days' }
  ];

  function handleChange(value: number) {
    selectedDays = value;
  }
</script>

<div class="chart-controls">
  {#each options as option}
    <button
      class="control-btn"
      class:active={selectedDays === option.value}
      on:click={() => handleChange(option.value)}
    >
      {option.label}
    </button>
  {/each}
</div>

<style>
  .chart-controls {
    display: flex;
    gap: 0.25rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
  }

  .control-btn {
    padding: 0.25rem 0.5rem;
    border: 1px solid #d1d5db;
    background: white;
    border-radius: 2px;
    font-size: 0.75rem;
    font-weight: 400;
    color: #374151;
    cursor: pointer;
    transition: all 0.15s ease;
    font-family: 'Georgia', 'Times New Roman', serif;
    letter-spacing: 0.01em;
  }

  .control-btn:hover {
    border-color: #374151;
    background: #f9fafb;
  }

  .control-btn.active {
    background: #374151;
    color: white;
    border-color: #374151;
    font-weight: 500;
  }

  .control-btn:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(55, 65, 81, 0.1);
  }
</style>
