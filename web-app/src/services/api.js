const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail || detail } catch { /* ignore */ }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  dashboard: () => request('/api/dashboard'),
  products: () => request('/api/products'),
  chat: (message, session_id, force_mode) =>
    request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id, ...(force_mode ? { force_mode } : {}) }),
    }),
  saveClaim: (id, subject, body) => request(`/api/claims/${id}`, { method: 'PUT', body: JSON.stringify({ subject, body }) }),
  draftClaim: (purchase_id, product_name, issue_description) =>
    request('/api/claims/draft', {
      method: 'POST',
      body: JSON.stringify({ purchase_id, product_name, issue_description }),
    }),
  removePurchase: (id) => request(`/api/purchases/${id}`, { method: 'DELETE' }),
  seed: () => request('/api/demo/seed', { method: 'POST' }),
}
