const API_ROOT = '/api/v1'
let accessToken = null
let csrfToken = null
let refreshPromise = null

export function setAccessToken(token) {
  accessToken = token || null
}

function getErrorMessage(payload, fallback) {
  if (typeof payload?.detail === 'string') return payload.detail
  const fieldNames = {
    username: 'Логин',
    password: 'Пароль',
    password_confirm: 'Повтор пароля',
    invite_code: 'Код приглашения',
    first_name: 'Имя',
    last_name: 'Фамилия',
    expires_in_hours: 'Срок действия',
    name: 'Название предмета',
  }
  if (payload && typeof payload === 'object') {
    for (const [field, messages] of Object.entries(payload)) {
      const message = Array.isArray(messages) ? messages[0] : messages
      if (typeof message === 'string') {
        return field === 'non_field_errors' ? message : `${fieldNames[field] || field}: ${message}`
      }
    }
  }
  return fallback
}

async function ensureCsrfToken() {
  if (csrfToken) return csrfToken

  let response
  try {
    response = await fetch(`${API_ROOT}/auth/csrf/`, { credentials: 'same-origin' })
  } catch {
    throw new Error('Не удалось связаться с сервером. Проверь, что Django запущен.')
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok || !payload?.csrf_token) {
    throw new Error(getErrorMessage(payload, 'Не удалось подготовить защищённый запрос.'))
  }
  csrfToken = payload.csrf_token
  return csrfToken
}

function isUnsafeMethod(method) {
  return !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes((method || 'GET').toUpperCase())
}

async function makeRequest(path, options, retrying = false) {
  const { json, ...fetchOptions } = options
  const headers = new Headers(fetchOptions.headers || {})
  const method = fetchOptions.method || 'GET'
  const isFormData = fetchOptions.body instanceof FormData

  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (isUnsafeMethod(method)) headers.set('X-CSRFToken', await ensureCsrfToken())
  if (json !== undefined) {
    headers.set('Content-Type', 'application/json')
    fetchOptions.body = JSON.stringify(json)
  } else if (isFormData) {
    headers.delete('Content-Type')
  }

  let response
  try {
    response = await fetch(`${API_ROOT}${path}`, {
      ...fetchOptions,
      method,
      headers,
      credentials: 'same-origin',
      cache: method.toUpperCase() === 'GET' ? 'no-store' : fetchOptions.cache,
    })
  } catch {
    throw new Error('Не удалось связаться с сервером. Проверь, что Django запущен.')
  }

  if (response.status === 401 && !retrying && !path.startsWith('/auth/')) {
    const refreshed = await refreshAccessToken()
    if (refreshed) return makeRequest(path, options, true)
    accessToken = null
    window.dispatchEvent(new Event('auth:expired'))
  }

  const payload = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(getErrorMessage(payload, `Ошибка запроса (${response.status}).`))
  }
  return payload
}

export function request(path, options = {}) {
  return makeRequest(path, options)
}

export async function refreshAccessToken() {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    try {
      const csrf = await ensureCsrfToken()
      const response = await fetch(`${API_ROOT}/auth/refresh/`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf },
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok || !payload?.access) return false
      accessToken = payload.access
      return true
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()
  return refreshPromise
}

export async function getFileBlob(url) {
  const fetchFile = () => fetch(url, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    credentials: 'same-origin',
    cache: 'no-store',
  })

  let response = await fetchFile()
  if (response.status === 401 && await refreshAccessToken()) response = await fetchFile()
  if (!response.ok) {
    if (response.status === 401) {
      accessToken = null
      window.dispatchEvent(new Event('auth:expired'))
    }
    throw new Error(response.status === 401 ? 'Сеанс завершился. Войди снова.' : 'Не удалось загрузить файл.')
  }
  return response.blob()
}

export async function downloadFile(url, filename) {
  const objectUrl = URL.createObjectURL(await getFileBlob(url))
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename || 'material'
  document.body.append(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
}

export const login = (credentials) => request('/auth/login/', { method: 'POST', json: credentials })
export const register = (data) => request('/auth/register/', { method: 'POST', json: data })
export const logout = () => request('/auth/logout/', { method: 'POST' })
export const getCurrentUser = () => request('/me/')
export const getHomeworks = () => request('/homework/')
export const getHomework = (id) => request(`/homework/${id}/`)
export const getSubjects = () => request('/subjects/')
export const createSubject = (data) => request('/subjects/', { method: 'POST', json: data })
export const updateSubject = (id, data) => request(`/subjects/${id}/`, { method: 'PATCH', json: data })
export const getSchedule = () => request('/schedule/')
export const createHomework = (data) => request('/homework/', { method: 'POST', json: data })
export const updateHomework = (id, data) => request(`/homework/${id}/`, { method: 'PATCH', json: data })
export function uploadHomeworkFiles(id, files) {
  const formData = new FormData()
  for (const file of files) formData.append('files', file, file.name)
  return request(`/homework/${id}/files/`, { method: 'POST', body: formData })
}
export const deleteHomework = (id) => request(`/homework/${id}/`, { method: 'DELETE' })
export const getInvites = () => request('/auth/invites/')
export const createInvite = (data) => request('/auth/invites/', { method: 'POST', json: data })
export const revokeInvite = (id) => request(`/auth/invites/${id}/`, { method: 'DELETE' })
