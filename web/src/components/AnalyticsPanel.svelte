<script>
  import { onMount } from 'svelte'
  import { activeView } from '$lib/view.js'

  let metrics = []
  let loading = true
  let error = null

  async function load() {
    loading = true
    try {
      const allRes = await fetch('/api/analytics/agents')
      if (allRes.status === 404) {
        metrics = []
        return
      }
      const allData = await allRes.json()
      metrics = allData
    } catch (e) {
      error = 'Failed to load analytics'
    } finally {
      loading = false
    }
  }

  onMount(load)

  function fmtRate(rate) {
    return `${(rate * 100).toFixed(1)}%`
  }

  function fmtDuration(ms) {
    if (!ms) return '—'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }
</script>

{#if loading}
  <p class="text-sm text-gray-500">جاري تحميل التحليلات...</p>
{:else if error}
  <p class="text-sm text-red-500">{error}</p>
{:else if metrics.length === 0}
  <p class="text-sm text-gray-500">لا توجد بيانات كافية بعد.</p>
{:else}
  <div class="overflow-x-auto">
    <table class="min-w-full text-sm">
      <thead>
        <tr class="border-b">
          <th class="text-right py-2 px-3">الوكيل</th>
          <th class="text-right py-2 px-3">معدل النجاح</th>
          <th class="text-right py-2 px-3">متوسط المدة</th>
          <th class="text-right py-2 px-3">التنفيذات</th>
          <th class="text-right py-2 px-3">مشاركات المجلس</th>
          <th class="text-right py-2 px-3">دروس التعلم</th>
        </tr>
      </thead>
      <tbody>
        {#each metrics as m}
          <tr class="border-b hover:bg-gray-50">
            <td class="py-2 px-3 font-medium">{m.agent_name}</td>
            <td class="py-2 px-3">{fmtRate(m.success_rate)}</td>
            <td class="py-2 px-3">{fmtDuration(m.average_duration_ms)}</td>
            <td class="py-2 px-3">{m.total_executions}</td>
            <td class="py-2 px-3">{m.council_participation_count}</td>
            <td class="py-2 px-3">{m.learning_entries_created}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
