import { writable } from 'svelte/store'

export const views = [
  { id: 'chat',        label: 'الدردشة',          icon: 'chat' },
  { id: 'notebooks',   label: 'دفاتر الملاحظات',  icon: 'book_4' },
  { id: 'models',      label: 'النماذج',          icon: 'smart_toy' },
  { id: 'lab',         label: 'المختبر',          icon: 'biotech' },
  { id: 'brand',       label: 'العلامة التجارية', icon: 'palette' },
  { id: 'operations',  label: 'العمليات',         icon: 'monitoring' },
  { id: 'settings',    label: 'الإعدادات',        icon: 'settings' },
]

function createView() {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('activeView') : null
  const initial = stored && views.find(v => v.id === stored) ? stored : 'chat'
  const { subscribe, set, update } = writable(initial)

  return {
    subscribe,
    set(id) {
      localStorage.setItem('activeView', id)
      set(id)
    },
  }
}

export const activeView = createView()
