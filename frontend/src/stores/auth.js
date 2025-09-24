// /Users/yuanjiayong/python/ai-chatbot/frontend/src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'
import { jwtDecode } from 'jwt-decode'

export const useAuthStore = defineStore('auth', () => {
  const access = ref(localStorage.getItem('access') || '')
  const refresh = ref(localStorage.getItem('refresh') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => {
    if (!access.value) return false
    try {
      const payload = jwtDecode(access.value)
      const now = Math.floor(Date.now() / 1000)
      return payload.exp > now
    } catch {
      return false
    }
  })

  function persist() {
    if (access.value) localStorage.setItem('access', access.value)
    else localStorage.removeItem('access')
    if (refresh.value) localStorage.setItem('refresh', refresh.value)
    else localStorage.removeItem('refresh')
    if (user.value) localStorage.setItem('user', JSON.stringify(user.value))
    else localStorage.removeItem('user')
  }

  async function login({ username, password }) {
    const { data } = await api.post('/api/login/', { username, password })
    access.value = data.access
    refresh.value = data.refresh
    user.value = { user_id: data.user_id, username: data.username }
    persist()
  }

  async function register({ username, password }) {
    await api.post('/api/register/', { username, password })
    await login({ username, password })
  }

  function logout() {
    access.value = ''
    refresh.value = ''
    user.value = null
    persist()
  }

  return {
    access, refresh, user, isAuthenticated,
    login, register, logout
  }
})
