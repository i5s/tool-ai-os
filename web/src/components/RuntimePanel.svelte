<script>
  import { onMount } from 'svelte'
  import { activeView } from '$lib/view.js'

  let jobs = []
  let loading = true
  let error = null

  async function load() {
    loading = true
    try {
      const res = await fetch('/api/runtime/jobs')
      if (res.status === 404) {
        jobs = []
        return
      }
      jobs = await res.json()
    } catch (e) {
      error = 'فشل تحميل المهام'
    } finally {
      loading = false
    }
  }

  onMount(load)

  function statusLabel(s) {
    const map = { pending: 'قيد الانتظار', assigned: 'مُعيَّن', running: 'قيد التنفيذ', completed: 'مكتمل', failed: 'فاشل' }
    return map[s] || s
  }
</script>

{#if loading}
  <p class="text-sm text-gray-500">جاري تحميل المهام...</p>
{:else if error}
  <p class="text-sm text-red-500">{error}</p>
{:else if jobs.length === 0}
  <p class="text-sm text-gray-500">لا توجد مهام وقتية بعد.</p>
{:else}
  <div class="overflow-x-auto">
    <table class="min-w-full text-sm">
      <thead>
        <tr class="border-b">
          <th class="text-right py-2 px-3">المهمة</th>
          <th class="text-right py-2 px-3">الحالة</th>
          <th class="text-right py-2 px-3">الخطة</th>
          <th class="text-right py-2 px-3">النتيجة المدمجة</th>
          <th class="text-right py-2 px-3">تاريخ الإنشاء</th>
        </tr>
      </thead>
      <tbody>
        {#each jobs as j}
          <tr class="border-b hover:bg-gray-50">
            <td class="py-2 px-3 font-medium">{j.id}</td>
            <td class="py-2 px-3">{statusLabel(j.status)}</td>
            <td class="py-2 px-3 text-xs">{j.plan_text || '—'}</td>
            <td class="py-2 px-3 text-xs">{j.merged_result || '—'}</td>
            <td class="py-2 px-3">{j.created_at}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
