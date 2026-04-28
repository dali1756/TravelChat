import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import RegisterPage from '../../src/pages/RegisterPage'
import * as AuthModule from '../../src/auth/AuthContext'
import { ApiError } from '../../src/lib/api'

function mockAuth(register: AuthModule.AuthContextValue['register']) {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    register,
    logout: vi.fn(),
  } as AuthModule.AuthContextValue)
}

function renderPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders email, username, password fields', () => {
    mockAuth(vi.fn())
    renderPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('shows verification prompt on success', async () => {
    const register = vi.fn().mockResolvedValue(undefined)
    mockAuth(register)
    renderPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@t.com' } })
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Aa1!xyzz' } })

    await act(async () => {
      screen.getByRole('button', { name: /register/i }).click()
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(register).toHaveBeenCalledWith({
      email: 'a@t.com',
      username: 'alice',
      password: 'Aa1!xyzz',
    })
    expect(screen.getByText(/請至信箱完成驗證/)).toBeInTheDocument()
  })

  it('shows field-level errors when backend returns 400', async () => {
    const register = vi.fn().mockRejectedValue(
      new ApiError(400, {
        email: ['email already taken'],
        password: ['Too short'],
      }),
    )
    mockAuth(register)
    renderPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@t.com' } })
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'x' } })

    await act(async () => {
      screen.getByRole('button', { name: /register/i }).click()
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(screen.getByText('email already taken')).toBeInTheDocument()
    expect(screen.getByText('Too short')).toBeInTheDocument()
  })
})
