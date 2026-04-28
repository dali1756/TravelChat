import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { auth } from '../../src/lib/auth'

const ORIGINAL_LOCATION = window.location

function mockLocation() {
  // jsdom forbids assigning window.location directly; replace with object
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { ...ORIGINAL_LOCATION, assign: vi.fn(), href: ORIGINAL_LOCATION.href },
  })
}

function restoreLocation() {
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: ORIGINAL_LOCATION,
  })
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiFetch', () => {
  beforeEach(() => {
    localStorage.clear()
    mockLocation()
    vi.resetModules()
  })

  afterEach(() => {
    restoreLocation()
    vi.restoreAllMocks()
  })

  it('attaches Authorization header when access token exists', async () => {
    auth.set('access-1', 'refresh-1')
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
    const { apiFetch } = await import('../../src/lib/api')

    await apiFetch('/api/members/me/')

    expect(fetchSpy).toHaveBeenCalledOnce()
    const init = fetchSpy.mock.calls[0][1] as RequestInit
    const headers = new Headers(init.headers)
    expect(headers.get('Authorization')).toBe('Bearer access-1')
  })

  it('refreshes on 401 and retries the original request once', async () => {
    auth.set('access-old', 'refresh-good')
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(200, { access: 'access-new', refresh: 'refresh-good' }))
      .mockResolvedValueOnce(jsonResponse(200, { id: 1 }))
    const { apiFetch } = await import('../../src/lib/api')

    const result = await apiFetch<{ id: number }>('/api/members/me/')

    expect(result).toEqual({ id: 1 })
    expect(fetchSpy).toHaveBeenCalledTimes(3)
    expect(auth.getAccess()).toBe('access-new')
    const retryInit = fetchSpy.mock.calls[2][1] as RequestInit
    expect(new Headers(retryInit.headers).get('Authorization')).toBe('Bearer access-new')
  })

  it('clears auth and redirects to /login when refresh also fails', async () => {
    auth.set('access-old', 'refresh-bad')
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'invalid refresh' }))
    const { apiFetch, ApiError } = await import('../../src/lib/api')

    await expect(apiFetch('/api/members/me/')).rejects.toBeInstanceOf(ApiError)
    expect(auth.getAccess()).toBeNull()
    expect(auth.getRefresh()).toBeNull()
    expect(window.location.assign).toHaveBeenCalledWith('/login')
  })

  it('does not refresh again if retried request still 401', async () => {
    auth.set('access-old', 'refresh-good')
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(200, { access: 'access-new', refresh: 'refresh-good' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'still expired' }))
    const { apiFetch, ApiError } = await import('../../src/lib/api')

    await expect(apiFetch('/api/members/me/')).rejects.toBeInstanceOf(ApiError)
    expect(fetchSpy).toHaveBeenCalledTimes(3)
  })

  it('dedupes concurrent refresh calls', async () => {
    auth.set('access-old', 'refresh-good')
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === 'string' ? input : input.toString()
        if (url.endsWith('/api/auth/token/refresh/')) {
          return Promise.resolve(jsonResponse(200, { access: 'access-new', refresh: 'refresh-good' }))
        }
        const headers = new Headers(init?.headers)
        const auth = headers.get('Authorization')
        if (auth === 'Bearer access-old') {
          return Promise.resolve(jsonResponse(401, { detail: 'expired' }))
        }
        return Promise.resolve(jsonResponse(200, { ok: true }))
      })
    const { apiFetch } = await import('../../src/lib/api')

    await Promise.all([apiFetch('/api/a/'), apiFetch('/api/b/'), apiFetch('/api/c/')])

    const refreshCalls = fetchSpy.mock.calls.filter(([input]) => {
      const url = typeof input === 'string' ? input : (input as URL | Request).toString()
      return url.endsWith('/api/auth/token/refresh/')
    })
    expect(refreshCalls.length).toBe(1)
  })

  it('throws ApiError carrying status and detail on non-2xx', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      jsonResponse(400, { email: ['email already taken'] }),
    )
    const { apiFetch, ApiError } = await import('../../src/lib/api')

    try {
      await apiFetch('/api/auth/register/', { method: 'POST', body: JSON.stringify({}) })
      expect.unreachable('expected ApiError')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      expect((err as InstanceType<typeof ApiError>).status).toBe(400)
      expect((err as InstanceType<typeof ApiError>).body).toEqual({
        email: ['email already taken'],
      })
    }
  })
})
