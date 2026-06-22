<script>
  import { api } from '../lib/store.js'
  import { onMount } from 'svelte'

  let tasks = $state([])
  let error = ''
  let loading = true
  let statusFilter = ''

  async function load() {
    try {
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      const qs = params.toString()
      tasks = await api.get(`/tasks${qs ? '?' + qs : ''}`)
    } catch (e) {
      error = e.message
    } finally {
      loading = false
    }
  }

  onMount(load)

  async function assignTask(task) {
    const agentId = prompt('Agent ID to assign:')
    if (!agentId) return
    await api.post(`/tasks/${task.id}/assign`, { agent_id: agentId })
    load()
  }

  async function startTask(task) {
    await api.post(`/tasks/${task.id}/start`, {})
    load()
  }

  async function completeTask(task) {
    await api.post(`/tasks/${task.id}/complete`, {})
    load()
  }

  async function failTask(task) {
    const reason = prompt('Failure reason:')
    await api.post(`/tasks/${task.id}/fail`, { error: reason })
    load()
  }

  async function removeTask(task) {
    if (!confirm('Delete task?')) return
    await api.delete(`/tasks/${task.id}`)
    load()
  }

  const statusLabel = { draft: 'مسودة', queued: 'قائمة انتظار', assigned: 'مُسند', running: 'قيد التنفيذ', completed: 'مكتمل', failed: 'فشل', cancelled: 'ألغيت' }
  const priorityLabel = { low: 'منخفض', medium: 'متوسط', high: 'مرتفع', critical: 'حرج' }
</script>

{#if loading}
  <div class="placeholder-panel"><p class="body-md" style="color:var(--text3)">جاري التحميل...</p></div>
{:else if error}
  <div class="placeholder-panel"><p class="body-md" style="color:var(--danger)">{error}</p></div>
{:else}
  <div class="panel">
    <div class="panel-header">
      <h2 class="body-lg" style="font-weight:600">المهام</h2>
      <div class="filters">
        <select class="select" bind:value={statusFilter} onchange={load}>
          <option value="">كل الحالات</option>
          <option value="draft">مسودة</option>
          <option value="queued">قائمة انتظار</option>
          <option value="assigned">مُسند</option>
          <option value="running">قيد التنفيذ</option>
          <option value="completed">مكتمل</option>
          <option value="failed">فشل</option>
          <option value="cancelled">ألغيت</option>
        </select>
        <button class="btn btn-secondary" onclick={load}>تحديث</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>العنوان</th>
            <th>الحالة</th>
            <th>الأولوية</th>
            <th>الوكيل المسند</th>
            <th>تاريخ الإنشاء</th>
            <th>آخر تحديث</th>
            <th>إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {#each tasks as t}
            <tr>
              <td>{t.title}</td>
              <td>{statusLabel[t.status] || t.status}</td>
              <td>{priorityLabel[t.priority] || t.priority}</td>
              <td>{t.assigned_agent_id || '—'}</td>
              <td>{new Date(t.created_at).toLocaleString('ar-SA')}</td>
              <td>{new Date(t.updated_at).toLocaleString('ar-SA')}</td>
              <td>
                <button class="btn btn-sm" onclick={() => assignTask(t)}>إسناد</button>
                <button class="btn btn-sm" onclick={() => startTask(t)}>بدء</button>
                <button class="btn btn-sm" onclick={() => completeTask(t)}>إكمال</button>
                <button class="btn btn-sm" onclick={() => failTask(t)}>إخفاق</button>
                <button class="btn btn-sm btn-danger" onclick={() => removeTask(t)}>حذف</button>
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
  .panel-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
  .filters { display: flex; gap: 8px; align-items: center; }
  .select { padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border2); background: var(--bg); color: var(--text); font-family: inherit; font-size: 0.85rem; }
  .table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface, #fff); }
  .table { width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 860px; }
  .table th, .table td { text-align: right; padding: 10px 12px; border-bottom: 1px solid var(--border); }
  .table th { color: var(--text2); font-weight: 600; background: var(--bg); }
  .btn { padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border2); background: var(--bg); color: var(--text); cursor: pointer; font-family: inherit; font-size: 0.8rem; }
  .btn:hover { background: var(--surface-hover); }
  .btn-sm { padding: 4px 8px; font-size: 0.75rem; }
  .btn-secondary { background: var(--bg); }
  .btn-danger { border-color: #f87171; color: #991b1b; }
  .btn-danger:hover { background: #fef2f2; }
</style>
