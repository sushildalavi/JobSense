import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@jobsense/types'
import { loginApi, getMeApi, logoutApi } from '@/api/auth'
import { API_BASE_URL } from '@/lib/constants'

interface AuthStore {
  user: User | null
  token: string | null
  isLoading: boolean
  isInitialized: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => void
  logout: () => void
  setUser: (user: User) => void
  setToken: (token: string) => void
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      isInitialized: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const tokenResponse = await loginApi({ email, password })
          const token = tokenResponse.access_token
          if (typeof window !== 'undefined') {
            localStorage.setItem('af_token', token)
          }
          set({ token })
          const user = await getMeApi()
          set({ user, token, isLoading: false })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      loginWithGoogle: () => {
        window.location.href = `${API_BASE_URL}/api/v1/auth/google`
      },

      logout: async () => {
        try {
          await logoutApi()
        } catch {
          // ignore
        } finally {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('af_token')
            localStorage.removeItem('af_user')
          }
          set({ user: null, token: null })
          window.location.href = '/login'
        }
      },

      setUser: (user: User) => set({ user }),
      setToken: (token: string) => set({ token }),

      initialize: async () => {
        const { token } = get()
        if (!token) {
          set({ isInitialized: true })
          return
        }
        set({ isLoading: true })
        try {
          const user = await getMeApi()
          set({ user, isLoading: false, isInitialized: true })
        } catch {
          set({ user: null, token: null, isLoading: false, isInitialized: true })
          if (typeof window !== 'undefined') {
            localStorage.removeItem('af_token')
          }
        }
      },
    }),
    {
      name: 'af_auth',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
)
