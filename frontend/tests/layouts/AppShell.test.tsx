import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AppShell from '../../src/layouts/AppShell'
import * as AuthModule from '../../src/auth/AuthContext'

function mockAuth(partial: Partial<AuthModule.AuthContextValue>) {
  const logout = vi.fn().mockResolvedValue(undefined)
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: { id: 1, username: 'jeter', email: 'j@test.com' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout,
    ...partial,
  } as AuthModule.AuthContextValue)
  return { logout }
}

function renderShell(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<div data-testid="child">CHILD</div>} />
        </Route>
        <Route path="/login" element={<div data-testid="login">LOGIN</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AppShell', () => {
  it('renders Navbar with current username and logout button', () => {
    mockAuth({})
    renderShell()
    expect(screen.getByText('jeter')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
  })

  it('renders the matched child via <Outlet />', () => {
    mockAuth({})
    renderShell()
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })

  it('clicking Logout calls auth.logout and navigates to /login', async () => {
    const { logout } = mockAuth({})
    renderShell()
    await act(async () => {
      screen.getByRole('button', { name: /logout/i }).click()
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(logout).toHaveBeenCalled()
    expect(await screen.findByTestId('login')).toBeInTheDocument()
  })
})
