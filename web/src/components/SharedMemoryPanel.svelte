<script>
  import { api } from '../lib/store.js'
  import { onMount } from 'svelte'

  let blocks = $state([])
  let error = ''
  let loading = true
  let scopeFilter = ''
  let searchQuery = ''

  async function load() {
    try {
      let result
      if (searchQuery.trim()) {
        result = await api.post(`/memory/search?q=${encodeURIComponent(searchQuery)}&limit=50`, {})
      } else {
        const params = new URLSearchParams()
        if (scopeFilter) params.set('scope', scopeFilter)
        const qs = params.toString()
        result = await api.get(`/memory${qs ? '?' + qs : ''}`)
      }
      blocks = result
    } catch (e) {
      error = e.message
    } finally {
      loading = false
    }
  }

  onMount(load)

  async function deleteBlock(id) {
    if (!confirm('حذف هذا البند؟')) return
    await api.delete(`/memory/${id}`)
    load()
  }

  const typeLabel = { fact: 'حقيقة', decision: 'قرار', artifact_ref: 'أثر', error: 'خطأ', hint: 'تلميح', constraint: 'قيودة' }
  const scopeLabel = { global: 'عام', project: 'مشروع', workspace: 'مساحة عمل', agent: 'وكيل' }
</script>

{#if loading}
  <div class="placeholder-panel"><p class="body-md" style="color:var(--text3)">جاري التحميل...</p></div>
{:else if error}
  <div class="placeholder-panel"><p class="body-md" style="color:var(--danger)">{error}</p></div>
{:else}
  <div class="panel">
    <div class="panel-header">
      <h2 class="body-lg" style="font-weight:600">الذاكرة المشتركة</h2>
      <div class="filters">
        <input class="input" placeholder="بحث..." bind:value={searchQuery} oninput={load} />
        <select class="select" bind:value={scopeFilter} onchange={load}>
          <option value="">كل النطاقات</option>
          <option value="global">عام</option>
          <option value="project">مشروع</option>
          <option value="workspace">مساحة عمل</option>
          <option value="agent">وكيل</option>
        </select>
        <button class="btn btn-secondary" onclick={load}>تحديث</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>العنوان</th>
            <th>النوع</th>
            <th>النطاق</th>
            <th>أنشئ بواسطة</th>
            <th>التاريخ</th>
            <th>إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {#each blocks as b}
            <tr>
              <td>{b.title}</td>
              <td>{typeLabel[b.type] || b.type}</td>
              <td>{scopeLabel[b.scope] || b.scope}{#if b.scope_id} ({b.scope_id}){/if}</td>
              <td>{b.created_by || '—'}</td>
              <td>{new Date(b.created_at).toLocaleString('ar-SA')}</td>
              <td>
                <button class="btn btn-sm btn-danger" onclick={() => deleteBlock(b.id)}>حذف</button>
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
  .input, .select { padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border2); background: var(--bg); color: var(--text); font-family: inherit; font-size: 0.85rem; }
  .table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface, #fff); }
  .table { width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 640px; }
  .table th, .table td { text-align: right; padding: 10px 12px; border-bottom: 1px solid var(--border); }
  .table th { color: var(--text2); font-weight: 600; background: var(--bg); }
  .btn-danger { border-color: #f87171; color: #991b1b; }
  .btn-danger:hover { background: #fef2f2; }
</style>
