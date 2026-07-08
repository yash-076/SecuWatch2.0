const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const ACCESS_TOKEN_KEY = 'secuwatch_access_token'
const REFRESH_TOKEN_KEY = 'secuwatch_refresh_token'

const TOKEN_KEYS = ['access_token', 'token', 'secuwatch_access_token']

function getAccessToken() {
  const primaryToken = window.localStorage.getItem(ACCESS_TOKEN_KEY)
  if (primaryToken) return primaryToken

  for (const key of TOKEN_KEYS) {
    const value = window.localStorage.getItem(key)
    if (value) return value
  }
  return null
}

function getRefreshToken() {
  return window.localStorage.getItem(REFRESH_TOKEN_KEY)
}

function setAccessToken(token) {
  if (!token) return
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

function setRefreshToken(token) {
  if (!token) return
  window.localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export function clearAuthTokens() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
  window.localStorage.removeItem(REFRESH_TOKEN_KEY)

  TOKEN_KEYS.forEach((key) => {
    window.localStorage.removeItem(key)
  })
}

export function hasAccessToken() {
  return Boolean(getAccessToken())
}

function formatApiError(detail) {
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((err) => {
        const field = err.loc && err.loc.length > 0 ? err.loc[err.loc.length - 1] : ''
        const message = err.msg || 'Invalid value'
        // Capitalize field name for better readability
        const fieldLabel = field ? field.charAt(0).toUpperCase() + field.slice(1) : ''
        return fieldLabel ? `${fieldLabel}: ${message}` : message
      })
      .join(', ')
  }
  if (typeof detail === 'object' && detail !== null) {
    if (detail.message) return detail.message
    if (detail.detail) return formatApiError(detail.detail)
    return JSON.stringify(detail)
  }
  return String(detail)
}

async function apiRequestInternal(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (options.withAuth !== false) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    const detail = payload?.detail || payload || `Request failed (${response.status})`
    throw {
      status: response.status,
      message: formatApiError(detail),
    }
  }

  return payload
}

let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  const payload = await apiRequestInternal('/auth/refresh', {
    method: 'POST',
    withAuth: false,
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  setAccessToken(payload.access_token)
  setRefreshToken(payload.refresh_token)
  return payload.access_token
}

async function apiRequest(path, options = {}) {
  try {
    return await apiRequestInternal(path, options)
  } catch (error) {
    const isUnauthorized = error?.status === 401
    const shouldRetry = isUnauthorized && options.withAuth !== false && !options._retried

    if (!shouldRetry) {
      if (isUnauthorized) {
        throw new Error('Unauthorized: login first to load live data.')
      }
      throw new Error(error?.message || 'Request failed')
    }

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken()
      }
      await refreshPromise
      refreshPromise = null
      return await apiRequest(path, { ...options, _retried: true })
    } catch (refreshError) {
      refreshPromise = null
      clearAuthTokens()
      throw new Error(refreshError?.message || 'Session expired. Please login again.')
    }
  }
}

export async function registerUser({ email, password, organization_name, role = 'analyst' }) {
  return apiRequest('/auth/register', {
    method: 'POST',
    withAuth: false,
    body: JSON.stringify({ email, password, organization_name, role }),
  })
}

export async function loginUser({ email, password }) {
  const tokens = await apiRequest('/auth/login', {
    method: 'POST',
    withAuth: false,
    body: JSON.stringify({ email, password }),
  })

  setAccessToken(tokens.access_token)
  setRefreshToken(tokens.refresh_token)
  return tokens
}

export async function getCurrentUser() {
  return apiRequest('/auth/me')
}

export async function logoutUser() {
  const refreshToken = getRefreshToken()
  if (refreshToken) {
    try {
      await apiRequest('/auth/logout', {
        method: 'POST',
        withAuth: false,
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
    } catch (_error) {
      // Ignore backend logout failures and still clear local session.
    }
  }
  clearAuthTokens()
}

export async function getAlerts({
  page = 1,
  limit = 100,
  severity,
  deviceId,
  fromTime,
  toTime,
  search,
  sortBy = 'created_at',
  order = 'desc',
} = {}) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
    sort_by: sortBy,
    order,
  })

  if (severity) params.set('severity', String(severity))
  if (deviceId) params.set('device_id', String(deviceId))
  if (fromTime) params.set('from_time', String(fromTime))
  if (toTime) params.set('to_time', String(toTime))
  if (search) params.set('search', String(search))

  return apiRequest(`/alerts?${params.toString()}`)
}

export async function getDevices() {
  return apiRequest('/devices')
}

export async function createDevice({ device_name, device_type }) {
  return apiRequest('/devices', {
    method: 'POST',
    body: JSON.stringify({ device_name, device_type }),
  })
}

export async function deleteDevice(deviceId) {
  return apiRequest(`/devices/${deviceId}`, {
    method: 'DELETE',
  })
}

export async function getDeviceConfig(deviceId) {
  return apiRequest(`/devices/${deviceId}/config`)
}

export async function updateDeviceConfig(deviceId, configData) {
  return apiRequest(`/devices/${deviceId}/config`, {
    method: 'PUT',
    body: JSON.stringify(configData),
  })
}

export async function getUsers() {
  return apiRequest('/auth/users')
}

export async function assignAlert(alertId, userId) {
  return apiRequest(`/alerts/${alertId}/assign`, {
    method: 'PATCH',
    body: JSON.stringify({ user_id: userId }),
  })
}

export async function assignAlertToMe(alertId) {
  return apiRequest(`/alerts/${alertId}/assign-to-me`, {
    method: 'PATCH',
  })
}

export async function updateAlertStatus(alertId, status) {
  return apiRequest(`/alerts/${alertId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function getWebSocketUrl() {
  const wsBaseUrl = API_BASE_URL.replace(/^http/, 'ws')
  const token = getAccessToken()
  return `${wsBaseUrl}/ws/alerts?token=${token || ''}`
}


export function mapSeverityLabel(value) {
  const normalized = String(value || '').toUpperCase()
  if (normalized === 'HIGH') return 'High'
  if (normalized === 'MEDIUM') return 'Medium'
  if (normalized === 'LOW') return 'Low'
  if (normalized === 'CRITICAL') return 'Critical'
  return 'Info'
}

export function mapStatusLabel(value) {
  const normalized = String(value || '').toUpperCase()
  if (normalized === 'IN_PROGRESS') return 'Investigating'
  if (normalized === 'RESOLVED') return 'Resolved'
  if (normalized === 'OPEN') return 'Open'
  if (normalized === 'ACKNOWLEDGED') return 'Acknowledged'
  return 'Open'
}

export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString()
}

export function formatTimeAgo(value) {
  if (!value) return 'Never'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  const diffMs = Date.now() - date.getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diffMs < minute) return 'Just now'
  if (diffMs < hour) return `${Math.floor(diffMs / minute)} mins ago`
  if (diffMs < day) return `${Math.floor(diffMs / hour)} hours ago`
  return `${Math.floor(diffMs / day)} days ago`
}

export function buildSeverityData(alerts) {
  const counts = { Critical: 0, High: 0, Medium: 0, Low: 0, Info: 0 }

  alerts.forEach((alert) => {
    const label = mapSeverityLabel(alert.severity)
    counts[label] = (counts[label] || 0) + 1
  })

  return Object.entries(counts).map(([name, value]) => ({ name, value }))
}

export function buildAlertsLineData(alerts) {
  const buckets = [
    { key: '00-04', start: 0, end: 4 },
    { key: '04-08', start: 4, end: 8 },
    { key: '08-12', start: 8, end: 12 },
    { key: '12-16', start: 12, end: 16 },
    { key: '16-20', start: 16, end: 20 },
    { key: '20-24', start: 20, end: 24 },
  ]

  const counts = Object.fromEntries(buckets.map((bucket) => [bucket.key, 0]))

  alerts.forEach((alert) => {
    const date = new Date(alert.created_at)
    if (Number.isNaN(date.getTime())) return

    const hour = date.getHours()
    const bucket = buckets.find((item) => hour >= item.start && hour < item.end)
    if (bucket) counts[bucket.key] += 1
  })

  return buckets.map((bucket) => ({ time: bucket.key, alerts: counts[bucket.key] }))
}

export function buildTopSourcesData(alerts) {
  const sourceCounts = {}

  alerts.forEach((alert) => {
    const source = `Device ${alert.device_id}`
    sourceCounts[source] = (sourceCounts[source] || 0) + 1
  })

  return Object.entries(sourceCounts)
    .map(([ip, count]) => ({ ip, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6)
}
