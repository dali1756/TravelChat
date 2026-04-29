import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { ApiError, apiFetch } from '../lib/api'
import { auth } from '../lib/auth'

export interface User {
  id: number
  username: string
  email: string
}

export interface RegisterPayload {
  email: string
  username: string
  password: string
  password_confirm: string
}

export interface AuthContextValue {
  currentUser: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login(email: string, password: string): Promise<void>
  register(payload: RegisterPayload): Promise<void>
  logout(): Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    let cancelled = false
    const access = auth.getAccess()
    if (!access) {
      setIsLoading(false)
      return
    }
    apiFetch<User>('/api/members/me/')
      .then((user) => {
        if (cancelled) return
        setCurrentUser(user)
      })
      .catch(() => {
        if (cancelled) return
        auth.clear()
        setCurrentUser(null)
      })
      .finally(() => {
        if (cancelled) return
        setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await apiFetch<{ access: string; refresh: string }>(
      '/api/auth/login/',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      },
    )
    auth.set(tokens.access, tokens.refresh)
    const user = await apiFetch<User>('/api/members/me/')
    setCurrentUser(user)
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    await apiFetch('/api/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }, [])

  const logout = useCallback(async () => {
    const refresh = auth.getRefresh()
    try {
      if (refresh) {
        await apiFetch('/api/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh }),
        })
      }
    } catch (err) {
      // Swallow — local logout MUST proceed regardless of backend response.
      if (err instanceof ApiError && err.status >= 500) {
        // optionally log; intentionally no rethrow
      }
    } finally {
      auth.clear()
      setCurrentUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      currentUser,
      isAuthenticated: currentUser !== null,
      isLoading,
      login,
      register,
      logout,
    }),
    [currentUser, isLoading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
