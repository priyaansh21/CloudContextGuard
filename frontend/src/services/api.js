/**
 * Centralized API client for the CloudContextGuard backend.
 *
 * Every network call the frontend makes goes through this module - no
 * component should build a fetch URL directly. The base URL is read from
 * VITE_API_BASE_URL so the frontend never hardcodes a host.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (cause) {
    throw new ApiError(`Could not reach ${API_BASE_URL}. Confirm the backend is running.`, 0)
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        detail = body.detail
      } else if (Array.isArray(body.detail)) {
        // FastAPI/Pydantic validation errors: a list of {loc, msg, ...}.
        detail = body.detail.map((err) => (err.loc ? `${err.loc.at(-1)}: ${err.msg}` : err.msg)).join('; ')
      }
    } catch {
      // response had no JSON body - fall back to statusText
    }
    throw new ApiError(detail, response.status)
  }

  if (response.status === 204) return null
  return response.json()
}

export function getHealth() {
  return request('/api/health')
}

export function getDashboard() {
  return request('/api/dashboard')
}

export function getUsers() {
  return request('/api/users')
}

export function getRoles() {
  return request('/api/roles')
}

export function getPermissions() {
  return request('/api/permissions')
}

export function getResources() {
  return request('/api/resources')
}

export function getVpcs() {
  return request('/api/vpcs')
}

export function getPolicies() {
  return request('/api/policies')
}

export function getPolicy(policyId) {
  return request(`/api/policies/${policyId}`)
}

export function updatePolicy(policyId, payload) {
  return request(`/api/policies/${policyId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getAccessRequests(limit = 200) {
  return request(`/api/access/requests?limit=${limit}`)
}

export function getSecurityEvents(limit = 200) {
  return request(`/api/security/events?limit=${limit}`)
}

export function getAlerts(limit = 200) {
  return request(`/api/alerts?limit=${limit}`)
}

export function submitAccessRequest(payload) {
  return request('/api/access/request', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
