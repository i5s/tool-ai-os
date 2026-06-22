import { writable } from 'svelte/store'

function createTheme() {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('theme') : null
  const initial = stored === 'light' ? 'light' : 'dark'
  const { subscribe, set, update } = writable(initial)

  return {
    subscribe,
    toggle() {
      update(current => {
        const next = current === 'dark' ? 'light' : 'dark'
        localStorage.setItem('theme', next)
        return next
      })
    },
    set,
  }
}

export const theme = createTheme()
