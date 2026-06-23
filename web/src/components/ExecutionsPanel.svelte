<script>
  import { onMount } from 'svelte'
  import { activeView } from '$lib/view.js'

  let records = []
  let loading = true
  let agentFilter = ''
  let taskFilter = ''
  let statusFilter = ''

  async function load() {
    loading = true
    const params = new URLSearchParams()
    if (agentFilter) params.set('agent_id', agentFilter)
    if (taskFilter) params.set('task_id', taskFilter)
    if (statusFilter) params.set('status', statusFilter)
    const url = `$api/executions?${params.toString()}`
    try {
      const res = await api.get(url)
      records = res || []
    } catch (e) {
      records = []
    } finally {
      loading = false
    }
  }

  onMount(() => {
    if ($activeView === 'executions') {
      load()
    }
  })

  function displayStatus(status) {
    return status || 'unknown'
  }

  async function deleteItem(path) {
    if (!confirm('Delete execution record?')) return
    await api.delete(path)
    await load()
  }
</script>

{#if $activeView === 'executions'}
  <div class="panel">
    <h2>سجل التنفيذ</h2>

    <div class="filters">
      <input placeholder="Agent ID" bind:value={agentFilter} />
      <input placeholder="Task ID" bind:value={taskFilter} />
      <select bind:value={statusFilter}>
        <option value="">All</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
      <button on:click={load}>Filter</button>
    </div>

    {#if loading}
      <p>Loading...</p>
    {:else if records.length === 0}
      <p>No executions found.</p>
    {:else}
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Task</th>
            <th>Agent</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Started</th>
            <th>Completed</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each records as ex}
            <tr>
              <td>{ex.id}</td>
              <td>{ex.task_id}</td>
              <td>{ex.agent_id}</td>
              <td>{displayStatus(ex.status)}</td>
              <td>{ex.duration_ms != null ? ex.duration_ms + 'ms' : '-'}</td>
              <td>{ex.started_at}</td>
              <td>{ex.completed_at || '-'}</td>
              <td>
                <button on:click={() => deleteItem(`/api/executions/${ex.id}`)}>Delete</button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
{/if}
