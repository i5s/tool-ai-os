<script>
  import { api } from '../lib/store.js'
  import { onMount } from 'svelte'

  let agents = $state([])
  let error = ''
  let loading = true

  async function load() {
    try {
      agents = await api.get('/agents')
    } catch (e) {
      error = e.message
    } finally {
      loading = false
    }
  }

  onMount(load)

  async function promote(id) {
    await api.post(`/agents/${id}/promote`)
    load()
  }

  async function demote(id) {
    await api.post(`/agents/${id}/demote`)
    load()
  }

  async function toggleStatus(id, current) {
    const next = current === 'active' ? 'disabled' : 'active'
    await api.put(`/agents/${id}`, { status: next })
    load()
  }

  const rankLabel = { leader: 'قائد', deputy: 'نائب', advisor: 'مستشار', worker: 'عامل' }
  const roleLabel = { architect: 'مهندس', developer: 'مطور', designer: 'مصمم', researcher: 'باحث', reviewer: 'مراجع', custom: 'مخصص' }
</script>

{#if loading}
  <div class="placeholder-panel">
    <p class="body-md" style="color:var(--text3)">جاري التحميل...</p>
  </div>
{:else if error}
  <div class="placeholder-panel">
    <p class="body-md" style="color:var(--danger)">{error}</p>
  </div>
{:else}
  <div class="panel">
    <div class="panel-header">
      <h2 class="body-lg" style="font-weight:600">فريق الذكاء الاصطناعي</h2>
      <button class="btn btn-secondary" onclick={load}>تحديث</button>
    </div>
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>الاسم</th>
            <th>الدور</th>
            <th>الرتبة</th>
            <th>الحالة</th>
            <th>السمعة</th>
            <th>إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {#each agents as a}
            <tr>
              <td>{a.name}</td>
              <td>{roleLabel[a.role] || a.role}</td>
              <td>{rankLabel[a.rank] || a.rank}</td>
              <td>
                <span class="status" class:status-active={a.status === 'active'} class:status-disabled={a.status === 'disabled'} class:status-experimental={a.status === 'experimental'}>
                  {a.status}
                </span>
              </td>
              <td>{a.reputation_score.toFixed(2)}</td>
              <td>
                <button class="btn btn-sm" onclick={() => promote(a.id)}>ترقية</button>
                <button class="btn btn-sm" onclick={() => demote(a.id)}>تخفيض</button>
                <button class="btn btn-sm" onclick={() => toggleStatus(a.id, a.status)}>{(a.status === 'active' ? 'تعطيل' : 'تفعيل')}</button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}

<style>
  .panel { padding: 24px; }
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }
  .table-wrap {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface, #fff);
  }
  .table { width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 640px; }
  .table th, .table td { text-align: right; padding: 10px 12px; border-bottom: 1px solid var(--border); }
  .table th { color: var(--text2); font-weight: 600; background: var(--bg); }
  .status { display: inline-block; padding: 4px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text2); }
  .status-active { border-color: #4ade80; color: #166534; }
  .status-disabled { border-color: #94a3b8; color: #475569; }
  .status-experimental { border-color: #fbbf24; color: #92400e; }
  .btn { cursor: pointer; font-family: inherit; border: 1px solid var(--border2); padding: 6px 12px; border-radius: 8px; font-size: 0.85rem; background: var(--bg); color: var(--text); transition: 0.15s; }
  .btn:hover { background: var(--surface-hover); }
  .btn-sm { padding: 4px 8px; font-size: 0.8rem; }
  .btn-secondary { background: var(--bg); }
</style>
