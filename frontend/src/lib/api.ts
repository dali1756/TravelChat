import { auth } from './auth'

const BASE_URL =
  (import.meta.env?.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown, message?: string) {
    super(message ?? extractDetail(body) ?? `Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function extractDetail(body: unknown): string | null {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return null
}

let refreshPromise: Promise<string | null> | null = null

async function tryRefresh(): Promise<string | null> {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    const refresh = auth.getRefresh()
    if (!refresh) return null
    try {
      const r = await fetch(`${BASE_URL}/api/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      if (!r.ok) return null
      const json = (await r.json()) as { access: string; refresh?: string }
      auth.set(json.access, json.refresh ?? refresh)
      return json.access
    } catch {
      return null
    } finally {
      refreshPromise = null
    }
  })()
  return refreshPromise
}

interface ApiFetchInit extends RequestInit {
  absolute?: boolean
  __retried?: boolean
}

export async function apiFetch<T = unknown>(
  input: string,
  init: ApiFetchInit = {},
): Promise<T> {
  const url = init.absolute ? input : `${BASE_URL}${input}`
  const headers = new Headers(init.headers)
  const access = auth.getAccess()
  if (access && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${access}`)
  }
  if (init.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(url, { ...init, headers })

  if (res.status === 401 && !init.__retried) {
    const newAccess = await tryRefresh()
    if (newAccess) {
      const retryHeaders = new Headers(headers)
      retryHeaders.set('Authorization', `Bearer ${newAccess}`)
      return apiFetch<T>(input, { ...init, headers: retryHeaders, __retried: true })
    }
    auth.clear()
    if (typeof window !== 'undefined') {
      window.location.assign('/login')
    }
    let body: unknown = null
    try {
      body = await res.json()
    } catch {
      // ignore
    }
    throw new ApiError(401, body, '認證失效，請重新登入。')
  }

  if (!res.ok) {
    let body: unknown = null
    try {
      body = await res.json()
    } catch {
      // ignore
    }
    throw new ApiError(res.status, body)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}
