const BASE = '/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, options = {}) {
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `Error ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Auth
  login: (username, password) =>
    request('/auth/token/', { method: 'POST', body: JSON.stringify({ username, password }) }),
  profile: () => request('/auth/profile/'),

  // Facilities
  getFacilities: () => request('/facilities/'),
  createFacility: (data) => request('/facilities/', { method: 'POST', body: JSON.stringify(data) }),

  // Batches
  getBatches: () => request('/batches/'),
  createBatch: (data) => request('/batches/', { method: 'POST', body: JSON.stringify(data) }),

  // Medications
  getMedications: () => request('/medications/'),
  logMedication: (data) => request('/medications/', { method: 'POST', body: JSON.stringify(data) }),

  // Waste
  getWaste: () => request('/waste/'),
  logWaste: (data) => request('/waste/', { method: 'POST', body: JSON.stringify(data) }),

  // Alerts
  getAlerts: () => request('/alerts/'),
  resolveAlert: (id) => request(`/alerts/${id}/resolve/`, { method: 'POST' }),

  // Dashboard
  getDashboard: () => request('/dashboard/'),

  // QR scan (public)
  scanQR: (code) => request(`/scan/${code}/`),
}
