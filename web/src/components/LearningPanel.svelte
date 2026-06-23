<script>
  import { onMount } from 'svelte'
  import { activeView } from '$lib/view.js'

  let entries = []
  let loading = true
  let sourceFilter = ''

  async function load() {
    loading = true
    try {
      const params = new URLSearchParams()
      if (sourceFilter) params.set('source_type', sourceFilter)
      const res = await fetch(`/api/learning?${params.toString()}`)
      if (res.ok) {
        entries = await res.json()
      }
    } catch (e) {
      entries = []
    } finally {
      loading = false
    }
  }

  async function refresh() {
    await load()
  }

  async function submitFeedback(id, type) {
    await fetch(`/api/learning/${id}/${type}`, { method: 'POST' })
    await refresh()
  }

  function fmtTime(iso) {
    if (!iso) return '-'
    const d = new Date(iso)
    return d.toLocaleString('ar-EG')
  }

  onMount(load)
</script>

<div class="panel">
  <div class="toolbar">
    <select bind:value={sourceFilter} on:change={refresh}>
      <option value="">جميع المصادر</option>
      <option value="execution">تنفيذ</option>
      <option value="council">مجلس</option>
      <option value="task">مهمة</option>
    </select>
  </div>

  {#if loading}
    <div class="empty">جاري التحميل...</div>
  {:else if entries.length === 0}
    <div class="empty">لا توجد دروس مسجلة</div>
  {:else}
    <table class="table">
      <thead>
        <tr>
          <th>الدرس</th>
          <th>المصدر</th>
          <th>العامل</th>
          <th>الثقة</th>
          <th>تاريخ الإنشاء</th>
          <th>الموافقات</th>
        </tr>
      </thead>
      <tbody>
        {#each entries as entry}
          <tr>
            <td class="title">{entry.title}</td>
            <td>{entry.source_type}</td>
            <td>{entry.agent_id}</td>
            <td>{Math.round((entry.confidence || 0) * 100)}%</td>
            <td>{fmtTime(entry.created_at)}</td>
            <td>
              <button class="btn" on:click={() => submitFeedback(entry.id, 'useful')}>مفيد</button>
              <button class="btn" on:click={() => submitFeedback(entry.id, 'ignored')}>متجاهل</button>
              <button class="btn" on:click={() => submitFeedback(entry.id, 'incorrect')}>خاطئ</button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>

<style>
  .panel { padding: 12px; }
  .toolbar { margin-bottom: 10px; display: flex; gap: 8px; }
  .table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { border: 1px solid #ddd; padding: 6px; text-align: right; }
  th { background: #f5f5f5; }
  .title { font-weight: 500; }
  .btn {
    background: #1976d2; color: #fff; border: none; padding: 4px 8px;
    border-radius: 4px; cursor: pointer; margin-left: 4px;
  }
  .btn:hover { background: #1565c0; }
  .empty { color: #888; text-align: center; padding: 20px; }
</style>
