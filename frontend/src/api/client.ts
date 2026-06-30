const BASE = '/api'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Accept': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, err.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

function formBody(data: Record<string, unknown>): RequestInit {
  const form = new URLSearchParams()
  for (const [k, v] of Object.entries(data)) {
    if (v != null) form.append(k, String(v))
  }
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: Record<string, unknown>) =>
    request<T>(path, data ? formBody(data) : { method: 'POST' }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
