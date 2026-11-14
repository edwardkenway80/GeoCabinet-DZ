// All requests go through Vite proxy → Django :8000
// CSRF token fetched once and cached; session cookie is httpOnly.

let _csrfToken: string | null = null

async function getCsrfToken(): Promise<string> {
  if (_csrfToken) return _csrfToken
  const res = await fetch('/api/v1/auth/csrf/', { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to fetch CSRF token')
  const data = await res.json()
  _csrfToken = data.csrfToken as string
  return _csrfToken
}

export function clearCsrfCache() { _csrfToken = null }

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  }
  if (method !== 'GET' && method !== 'HEAD') {
    headers['X-CSRFToken'] = await getCsrfToken()
  }
  const res = await fetch(url, {
    method,
    credentials: 'include',
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return undefined as T

  const contentType = res.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')

  if (!isJson) {
    const text = await res.text().catch(() => '')
    throw new Error(
      `الاستجابة غير متوقعة من الخادم (HTTP ${res.status}) للمسار: ${url}\n${text.slice(0, 200)}`
    )
  }

  const json = await res.json()
  if (!res.ok) throw new Error(json?.detail ?? json?.message ?? `HTTP ${res.status}`)
  return json as T
}

export const api = {
  get:    <T>(url: string)               => request<T>('GET',    url),
  post:   <T>(url: string, body: unknown) => request<T>('POST',   url, body),
  patch:  <T>(url: string, body: unknown) => request<T>('PATCH',  url, body),
  delete: <T>(url: string)               => request<T>('DELETE', url),
}
