import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import LoginPage from '../../src/pages/LoginPage'
import * as AuthModule from '../../src/auth/AuthContext'
import { ApiError } from '../../src/lib/api'

function mockAuth(partial: Partial<AuthModule.AuthContextValue>) {
  const login = vi.fn().mockResolvedValue(undefined)
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: null,
    isAuthenticated: false,
    isLoading: false,
    login,
    register: vi.fn(),
    logout: vi.fn(),
    ...partial,
  } as AuthModule.AuthContextValue)
  return { login }
}

function renderPage(initialEntries: Array<string | { pathname: string; state?: unknown }> = ['/login']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<div data-testid="home">HOME</div>} />
        <Route path="/_styleguide" element={<div data-testid="sg">SG</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders email + password fields and submit button', () => {
    mockAuth({})
    renderPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('calls login() and navigates to / on success', async () => {
    const { login } = mockAuth({})
    renderPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@t.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'pw' } })

    await act(async () => {
      screen.getByRole('button', { name: /login/i }).click()
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(login).toHaveBeenCalledWith('a@t.com', 'pw')
    expect(await screen.findByTestId('home')).toBeInTheDocument()
  })

  it('navigates to state.from when provided', async () => {
    mockAuth({})
    renderPage([{ pathname: '/login', state: { from: '/_styleguide' } }])
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@t.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'pw' } })
    await act(async () => {
      screen.getByRole('button', { name: /login/i }).click()
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(await screen.findByTestId('sg')).toBeInTheDocument()
  })

  it('shows error message when login fails', async () => {
    const login = vi.fn().mockRejectedValue(
      new ApiError(401, { detail: 'Email 或密碼錯誤。' }),
    )
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      currentUser: null,
      isAuthenticated: false,
      isLoading: false,
      login,
      register: vi.fn(),
      logout: vi.fn(),
    } as AuthModule.AuthContextValue)

    renderPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@t.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'bad' } })
    await act(async () => {
      screen.getByRole('button', { name: /login/i }).click()
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(screen.getByText(/Email 或密碼錯誤/)).toBeInTheDocument()
  })

  it('redirects to / if already authenticated', () => {
    mockAuth({
      isAuthenticated: true,
      currentUser: { id: 1, username: 'u', email: 'u@t' },
    })
    renderPage()
    expect(screen.getByTestId('home')).toBeInTheDocument()
  })
})
