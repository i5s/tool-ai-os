<script>
  import { onMount } from 'svelte'
  import { activeView } from '$lib/view.js'

  let board = []
  let loading = true
  let error = null

  async function load() {
    loading = true
    try {
      const res = await fetch('/api/reputation/leaderboard?limit=20')
      if (res.status === 404) {
        board = []
        return
      }
      board = await res.json()
    } catch (e) {
      error = 'فشل تحميل السمعة'
    } finally {
      loading = false
    }
  }

  onMount(load)

  function rankLabel(rank) {
    const map = { leader: 'قائد', deputy: 'نائب', advisor: 'مستشار', worker: 'عامل' }
    return map[rank] || rank
  }

  function scoreClass(score) {
    if (score >= 0.9) return 'text-green-600 font-semibold'
    if (score >= 0.7) return 'text-blue-600'
    if (score >= 0.4) return 'text-yellow-600'
    return 'text-gray-500'
  }
</script>

{#if loading}
  <p class="text-sm text-gray-500">جاري تحميل السمعة...</p>
{:else if error}
  <p class="text-sm text-red-500">{error}</p>
{:else if board.length === 0}
  <p class="text-sm text-gray-500">لا توجد بيانات كافية بعد.</p>
{:else}
  <div class="overflow-x-auto">
    <table class="min-w-full text-sm">
      <thead>
        <tr class="border-b">
          <th class="text-right py-2 px-3">الوكيل</th>
          <th class="text-right py-2 px-3">السمعة</th>
          <th class="text-right py-2 px-3">الجودة</th>
          <th class="text-right py-2 px-3">السرعة</th>
          <th class="text-right py-2 px-3">الموثوقية</th>
          <th class="text-right py-2 px-3">التعلم</th>
          <th class="text-right py-2 px-3">المجلس</th>
          <th class="text-right py-2 px-3">الرتبة المقترحة</th>
        </tr>
      </thead>
      <tbody>
        {#each board as b}
          <tr class="border-b hover:bg-gray-50">
            <td class="py-2 px-3 font-medium">{b.agent_id}</td>
            <td class="py-2 px-3 {scoreClass(b.reputation_score)}">{(b.reputation_score * 100).toFixed(1)}%</td>
            <td class="py-2 px-3">{(b.quality_score * 100).toFixed(1)}%</td>
            <td class="py-2 px-3">{(b.speed_score * 100).toFixed(1)}%</td>
            <td class="py-2 px-3">{(b.reliability_score * 100).toFixed(1)}%</td>
            <td class="py-2 px-3">{(b.learning_score * 100).toFixed(1)}%</td>
            <td class="py-2 px-3">{(b.council_score * 100).toFixed(1)}%</td>
            <td class="py-2 px-3">{rankLabel(b.recommended_rank)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
