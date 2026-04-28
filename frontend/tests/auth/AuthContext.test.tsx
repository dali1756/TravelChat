import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { AuthProvider, useAuth } from '../../src/auth/AuthContext'
import { auth } from '../../src/lib/auth'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function Probe() {
  const { isAuthenticated, isLoading, currentUser } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="auth">{String(isAuthenticated)}</span>
      <span data-testid="user">{currentUser ? currentUser.username : 'none'}</span>
    </div>
  )
}

async function renderProvider() {
  const utils = render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
  // wait for initial async settle
  await act(async () => {
    await Promise.resolve()
    await Promise.resolve()
  })
  return utils
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('starts unauthenticated when no token in storage', async () => {
    await renderProvider()
    expect(screen.getByTestId('loading')).toHaveTextContent('false')
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('restores session on mount when access token is stored', async () => {
    auth.set('a', 'r')
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      jsonResponse(200, { id: 1, username: 'jeter', email: 'j@test.com' }),
    )
    await renderProvider()
    expect(screen.getByTestId('auth')).toHaveTextContent('true')
    expect(screen.getByTestId('user')).toHaveTextContent('jeter')
  })

  it('clears storage when restore fails (token invalid + refresh fails)', async () => {
    auth.set('a', 'r-bad')
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'invalid refresh' }))
    await renderProvider()
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(auth.getAccess()).toBeNull()
  })

  it('login() stores tokens, fetches profile, sets currentUser', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(200, { access: 'a', refresh: 'r' }))
      .mockResolvedValueOnce(jsonResponse(200, { id: 2, username: 'alice', email: 'a@test.com' }))

    function Trigger() {
      const { login, isAuthenticated, currentUser } = useAuth()
      return (
        <>
          <button onClick={() => login('a@test.com', 'pw')}>do</button>
          <span data-testid="auth">{String(isAuthenticated)}</span>
          <span data-testid="user">{currentUser?.username ?? 'none'}</span>
        </>
      )
    }

    render(
      <AuthProvider>
        <Trigger />
      </AuthProvider>,
    )
    await act(async () => {
      await Promise.resolve()
    })
    await act(async () => {
      screen.getByText('do').click()
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(screen.getByTestId('auth')).toHaveTextContent('true')
    expect(screen.getByTestId('user')).toHaveTextContent('alice')
    expect(auth.getAccess()).toBe('a')
  })

  it('register() does not write tokens or change auth state', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      jsonResponse(201, { detail: 'Verification email sent.' }),
    )

    function Trigger() {
      const { register, isAuthenticated } = useAuth()
      return (
        <>
          <button
            onClick={() => register({ email: 'b@t.com', username: 'b', password: 'Aa1!xyzz' })}
          >
            r
          </button>
          <span data-testid="auth">{String(isAuthenticated)}</span>
        </>
      )
    }

    render(
      <AuthProvider>
        <Trigger />
      </AuthProvider>,
    )
    await act(async () => {
      await Promise.resolve()
    })
    await act(async () => {
      screen.getByText('r').click()
      await Promise.resolve()
    })
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(auth.getAccess()).toBeNull()
  })

  it('logout() clears local state even if backend call fails', async () => {
    auth.set('a', 'r')
    vi.spyOn(globalThis, 'fetch')
      // initial profile fetch
      .mockResolvedValueOnce(jsonResponse(200, { id: 1, username: 'u', email: 'u@t.com' }))
      // logout call rejects
      .mockRejectedValueOnce(new TypeError('network'))

    function Trigger() {
      const { logout, isAuthenticated } = useAuth()
      return (
        <>
          <button onClick={() => logout()}>x</button>
          <span data-testid="auth">{String(isAuthenticated)}</span>
        </>
      )
    }
    render(
      <AuthProvider>
        <Trigger />
      </AuthProvider>,
    )
    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })
    await act(async () => {
      screen.getByText('x').click()
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(auth.getAccess()).toBeNull()
  })
})
