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
    background: #ffffff;
    border: 1px solid #000000;
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  h2 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .chart-area {
    position: relative;
    width: 100%;
    flex: 1;
  }
</style>