<script lang="ts">
    export let title: string = '';
    export let height: string = '320px';
</script>

<div class="card">
    {#if title}
        <h2>{title}</h2>
    {/if}
    <div class="chart-area" style="height: {height};">
        <slot />
    </div>
</div>

<style>
  .card {
    background: #fefdfb;
    border: 1px solid #d6d3d1;
    border-radius: 2px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  }

  h2 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 400;
    color: #1c1917;
    letter-spacing: 0.02em;
    font-family: 'Georgia', 'Times New Roman', serif;
    text-transform: uppercase;
    border-bottom: 1px solid #e7e5e4;
    padding-bottom: 0.5rem;
  }

  .chart-area {
    position: relative;
    width: 100%;
    flex: 1;
    min-height: 0;
  }
</style>