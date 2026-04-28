import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../../src/auth/ProtectedRoute'
import * as AuthModule from '../../src/auth/AuthContext'

function setAuth(value: Partial<AuthModule.AuthContextValue>) {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...value,
  } as AuthModule.AuthContextValue)
}

function renderWithRouter(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="/secret"
          element={
            <ProtectedRoute>
              <div data-testid="secret">SECRET</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div data-testid="login-page">LOGIN</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated user to /login', () => {
    setAuth({ isAuthenticated: false, isLoading: false })
    renderWithRouter('/secret')
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByTestId('secret')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    setAuth({
      isAuthenticated: true,
      isLoading: false,
      currentUser: { id: 1, username: 'u', email: 'u@t' },
    })
    renderWithRouter('/secret')
    expect(screen.getByTestId('secret')).toBeInTheDocument()
  })

  it('renders loading indicator while isLoading', () => {
    setAuth({ isAuthenticated: false, isLoading: true })
    const { container } = renderWithRouter('/secret')
    expect(container.querySelector('[data-testid="protected-loading"]')).not.toBeNull()
    expect(screen.queryByTestId('secret')).not.toBeInTheDocument()
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
  })
})
