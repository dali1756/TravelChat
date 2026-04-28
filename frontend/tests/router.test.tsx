import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import * as AuthModule from '../src/auth/AuthContext'
import { AppRoutes } from '../src/router'

function mockAuth(authenticated: boolean) {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: authenticated ? { id: 1, username: 'jeter', email: 'j@t' } : null,
    isAuthenticated: authenticated,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  } as AuthModule.AuthContextValue)
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

describe('AppRoutes', () => {
  it('redirects unauthenticated user from / to /login', () => {
    mockAuth(false)
    renderAt('/')
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('redirects unauthenticated user from /_styleguide to /login', () => {
    mockAuth(false)
    renderAt('/_styleguide')
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('renders styleguide for authenticated user at /_styleguide', () => {
    mockAuth(true)
    renderAt('/_styleguide')
    expect(screen.getByText(/Travel Chat — Design System/)).toBeInTheDocument()
  })

  it('redirects authenticated user from / to /_styleguide', () => {
    mockAuth(true)
    renderAt('/')
    expect(screen.getByText(/Travel Chat — Design System/)).toBeInTheDocument()
  })
})
