<script>
  let statuses = []
  let loading = true
  let error = null
  let lastUpdated = null

  async function loadHealth() {
    loading = true
    try {
      const [runtime, agents, mcp, database, providers] = await Promise.all([
        fetch('/api/health/runtime').then(r => r.json()),
        fetch('/api/health/agents').then(r => r.json()),
        fetch('/api/health/mcp').then(r => r.json()),
        fetch('/api/health/database').then(r => r.json()),
        fetch('/api/health/providers').then(r => r.json()),
      ])
      statuses = [
        {title: 'Runtime', data: runtime},
        {title: 'Agents', data: agents},
        {title: 'MCP', data: mcp},
        {title: 'Database', data: database},
        {title: 'Providers', data: providers},
      ]
      lastUpdated = new Date().toLocaleTimeString('ar-EG')
    } catch (e) {
      error = 'فشل تحميل بيانات الصحة'
    } finally {
      loading = false
    }
  }

  function statusColor(status) {
    const s = (status || '').toLowerCase()
    if (s === 'ok') return '#22c55e'
    if (s === 'degraded') return '#f59e0b'
    if (s === 'disabled') return '#94a3b8'
    if (s === 'error') return '#ef4444'
    return '#94a3b8'
  }

  function latencyBadge(ms) {
    if (ms == null) return '-'
    if (ms < 200) return `${ms}ms`
    if (ms < 1000) return `${ms}ms`
    return `${ms}ms`
  }
</script>

<div class="health-panel">
  <div class="panel-header">
    <span class="panel-title">Health Dashboard</span>
    <button class="text-btn" onclick={loadHealth} disabled={loading}>تحديث</button>
  </div>
  {#if loading}
    <div class="placeholder">جاري التحميل…</div>
  {:else if error}
    <div class="error">{error}</div>
  {:else}
    <div class="cards">
      {#each statuses as item}
        <div class="card">
          <div class="card-header">
            <span class="card-title">{item.title}</span>
            <span class="status-badge" style="background:{statusColor(item.data.status)}">{item.data.status || 'n/a'}</span>
          </div>
          <div class="card-body">
            {#if item.title === 'Agents'}
              {#each Object.values(item.data.agents || {}) as agent}
                <div class="row">
                  <span class="label">{agent.name}</span>
                  <span class="badge" style="background:{statusColor(agent.status)}">{agent.status}</span>
                  <span class="muted">{latencyBadge(agent.last_response_time_ms)}</span>
                </div>
              {/each}
            {:else if item.title === 'Providers'}
              {#each Object.entries(item.data.providers || {}) as [key, provider]}
                <div class="row">
                  <span class="label">{key}</span>
                  <span class="muted">{provider.type}</span>
                  <span class="badge" style="background:{statusColor(provider.available ? 'ok' : 'error')}">
                    {provider.available ? 'ok' : 'error'}
                  </span>
                </div>
              {/each}
            {:else if item.title === 'MCP'}
              {#each Object.entries(item.data.servers || {}) as [key, server]}
                <div class="row">
                  <span class="label">{key}</span>
                  <span class="badge" style="background:{statusColor(server.available ? 'ok' : 'error')}">
                    {server.available ? 'ok' : 'error'}
                  </span>
                  <span class="muted">{latencyBadge(server.duration_ms)}</span>
                </div>
              {/each}
            {:else if item.title === 'Database'}
              <div class="row">
                <span class="label">connection</span>
                <span class="badge" style="background:{statusColor('ok')}">ok</span>
              </div>
              <div class="row">
                <span class="label">tables</span>
                <span class="muted">{item.data.table_count ?? '-'}</span>
              </div>
            {:else}
              <div class="row">
                <span class="label">running</span>
                <span class="muted">{item.data.running_jobs ?? '-'}</span>
              </div>
              <div class="row">
                <span class="label">queued</span>
                <span class="muted">{item.data.queued_jobs ?? '-'}</span>
              </div>
              <div class="row">
                <span class="label">failed</span>
                <span class="muted">{item.data.failed_jobs ?? '-'}</span>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
    <div class="footer">
      <span>آخر تحديث: {lastUpdated || '-'}</span>
    </div>
  {/if}
</div>

<style>
  .health-panel {
    padding: 18px;
  }
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  .panel-title {
    font-weight: 600;
    font-size: 1rem;
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
  }
  .card {
    border: 1px solid var(--border, #e5e7eb);
    border-radius: 12px;
    padding: 12px;
    background: var(--surface, #fff);
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .card-title {
    font-weight: 600;
  }
  .status-badge {
    color: #fff;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.75rem;
    text-transform: uppercase;
  }
  .card-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }
  .label {
    color: var(--text2, #374151);
    font-size: 0.85rem;
  }
  .muted {
    color: var(--text3, #6b7280);
    font-size: 0.8rem;
  }
  .badge {
    color: #fff;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.7rem;
    text-transform: uppercase;
  }
  .error {
    color: #ef4444;
    font-size: 0.9rem;
  }
  .placeholder {
    color: var(--text3, #6b7280);
    font-size: 0.9rem;
  }
  .text-btn {
    border: 1px solid var(--border, #e5e7eb);
    background: none;
    padding: 4px 10px;
    border-radius: 8px;
    color: var(--text, #111827);
    cursor: pointer;
  }
  .text-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .footer {
    margin-top: 10px;
    font-size: 0.75rem;
    color: var(--text3, #6b7280);
  }
</style>
