import { reactive } from 'vue'
import { getCurrentUser, login, logout, refreshAccessToken, register, setAccessToken } from '@/services/api'

export const authState = reactive({
  user: null,
  initialized: false,
})

let restorePromise = null

export function clearSession() {
  setAccessToken(null)
  authState.user = null
  authState.initialized = true
}

export async function signIn(credentials) {
  const tokens = await login(credentials)
  setAccessToken(tokens.access)
  try {
    authState.user = await getCurrentUser()
    authState.initialized = true
    return authState.user
  } catch (error) {
    clearSession()
    throw error
  }
}

export async function signUp(form) {
  return register(form)
}

export async function signOut() {
  try {
    await logout()
  } finally {
    clearSession()
  }
}

export function restoreSession() {
  if (authState.initialized) return Promise.resolve()
  if (restorePromise) return restorePromise

  restorePromise = (async () => {
    try {
      if (await refreshAccessToken()) authState.user = await getCurrentUser()
    } catch {
      clearSession()
    } finally {
      authState.initialized = true
      restorePromise = null
    }
  })()

  return restorePromise
}
