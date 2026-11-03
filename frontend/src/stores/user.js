import { defineStore } from 'pinia'
import { TOKEN_KEY } from '@/api/http'
import { fetchCurrentUser, login as loginApi, register as registerApi, updateProfile } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    profile: null,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    isAdmin: (state) => state.profile?.role === 'admin',
    displayName: (state) => state.profile?.nickname || state.profile?.username || '',
  },
  actions: {
    async login(payload) {
      const data = await loginApi(payload)
      this.token = data.access_token
      this.profile = data.user
      localStorage.setItem(TOKEN_KEY, data.access_token)
      return data
    },
    async register(payload) {
      return registerApi(payload)
    },
    /** 刷新页面后 store 是空的，需要用令牌把资料取回来 */
    async loadProfile({ silent = true } = {}) {
      if (!this.token) return null
      const data = await fetchCurrentUser({ silent })
      this.profile = data
      return data
    },
    async saveProfile(payload) {
      const data = await updateProfile(payload)
      this.profile = data
      return data
    },
    logout() {
      this.token = ''
      this.profile = null
      localStorage.removeItem(TOKEN_KEY)
    },
    /** 401 拦截器只清了 localStorage，这里同步清掉 store，避免界面还显示已登录 */
    handleExpired() {
      if (this.token || this.profile) this.logout()
    },
  },
})
