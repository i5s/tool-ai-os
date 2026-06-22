import { writable } from 'svelte/store'

export const api = {
  async get(path) {
    const res = await fetch(`/api${path}`)
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
    return res.json()
  },
  async post(path, body) {
    const res = await fetch(`/api${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
    return res.json()
  },
}

export const conversations = writable([])
export const workspaces = writable({ brands: [], universities: [], projects: [], semesters: [] })
