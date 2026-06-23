<script>
  import { onMount } from 'svelte'
  import { activeView } from '$lib/view.js'

  let sessions = []
  let current = null
  let loading = true
  let taskFilter = ''
  let statusFilter = ''

  async function loadSessions() {
    loading = true
    const params = new URLSearchParams()
    if (taskFilter) params.set('task_id', taskFilter)
    if (statusFilter) params.set('status', statusFilter)
    const url = `$api/council?${params.toString()}`
    try {
      const res = await api.get(url)
      sessions = res || []
    } finally {
      loading = false
    }
  }

  async function selectSession(id) {
    loading = true
    try {
      const res = await api.get(`$api/council/${id}`)
      current = res
    } finally {
      loading = false
    }
  }

  onMount(() => {
    if ($activeView === 'council') {
      loadSessions()
    }
  })

  async function createSession() {
    const title = prompt('Session title (optional)')
    const strategy = confirm('Use consensus strategy? Cancel = majority') ? 'consensus' : 'majority'
    const body = {
      strategy,
      member_ids: ['Hermes', 'OpenCode'],
    }
    if (title) {
      body.task_id = title
    }
    await api.post('$api/council', body)
    await loadSessions()
  }

  async function vote(sessionId, agentId, vote) {
    await api.post(`$api/council/${sessionId}/vote`, { agent_id: agentId, vote, confidence: 0.8 })
    await selectSession(sessionId)
  }

  async function finalize(sessionId) {
    await api.post(`$api/council/${sessionId}/finalize`, {})
    await selectSession(sessionId)
    await loadSessions()
  }

  function statusColor(s) {
    return s === 'completed' ? 'green' : s === 'voting' ? 'yellow' : s === 'failed' ? 'red' : 'gray'
  }
</script>

{#if $activeView === 'council'}
  <div class="panel">
    <h2>Council</h2>

    <div class="filters">
      <input placeholder="Task ID" bind:value={taskFilter} />
      <select bind:value={statusFilter}>
        <option value="">All</option>
        <option value="open">Open</option>
        <option value="voting">Voting</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
      <button on:click={loadSessions}>Refresh</button>
      <button on:click={createSession}>New Session</button>
    </div>

    {#if loading && !current}
      <p>Loading...</p>
    {:else if sessions.length === 0}
      <p>No council sessions found.</p>
    {:else}
      <div class="sessions">
        {#each sessions as s}
          <div class="session-card" class:active={current && current.session && current.session.id === s.id} on:click={() => selectSession(s.id)}>
            <strong>{s.id}</strong>
            <span class="status-badge {statusColor(s.status)}">{s.status}</span>
            <small>{s.task_id || 'no-task'}</small>
          </div>
        {/each}
      </div>
    {/if}

    {#if current}
      <div class="detail">
        <h3>Session {current.session.id}</h3>
        <p>Status: <span class="status-badge {statusColor(current.session.status)}">{current.session.status}</span></p>
        <p>Strategy: {current.session.strategy}</p>
        <p>Task: {current.session.task_id || 'none'}</p>

        <h4>Members</h4>
        <ul>
          {#each current.members || [] as m}
            <li>{m.agent_name || m.agent_id} ({m.role})</li>
          {/each}
        </ul>

        <h4>Votes</h4>
        <ul>
          {#each current.votes || [] as v}
            <li>{v.agent_name || v.agent_id}: {v.vote} (confidence {v.confidence})</li>
          {/each}
        </ul>

        {#if current.session.status === 'open' || current.session.status === 'voting'}
          <button on:click={() => vote(current.session.id, 'Hermes', 'approve')}>Hermes: Approve</button>
          <button on:click={() => vote(current.session.id, 'Hermes', 'reject')}>Hermes: Reject</button>
          <button on:click={() => vote(current.session.id, 'OpenCode', 'approve')}>OpenCode: Approve</button>
          <button on:click={() => vote(current.session.id, 'OpenCode', 'reject')}>OpenCode: Reject</button>
        {/if}

        {#if !current.decision && (current.session.status === 'voting' || current.session.status === 'open')}
          <button class="primary" on:click={() => finalize(current.session.id)}>Finalize</button>
        {/if}

        {#if current.decision}
          <h4>Decision</h4>
          <p>Winner: {current.decision.winning_agent_name || current.decision.winning_agent_id}</p>
          <p>{current.decision.decision_summary}</p>
          <p><small>{current.decision.rationale}</small></p>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .sessions {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 8px;
    margin-bottom: 16px;
  }
  .session-card {
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
    cursor: pointer;
    background: var(--bg);
  }
  .session-card.active {
    border-color: var(--primary);
    background: var(--surface-hover);
  }
  .session-card h4 {
    margin: 0;
    font-size: 0.9rem;
  }
  .status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    color: white;
    margin-left: 6px;
  }
  .status-badge.green { background: #16a34a; }
  .status-badge.yellow { background: #ca8a04; }
  .status-badge.red { background: #dc2626; }
  .status-badge.gray { background: #6b7280; }
  .detail {
    border-top: 1px solid var(--border);
    padding-top: 12px;
  }
  button.primary {
    background: var(--primary);
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
  }
  button.primary:hover {
    opacity: 0.9;
  }
</style>
