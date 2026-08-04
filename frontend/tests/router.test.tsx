import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import * as AuthModule from '../src/auth/AuthContext'
import * as tripApi from '../src/lib/tripApi'
import { AppRoutes, router } from '../src/router'

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

function collectPaths(routes: readonly { path?: string; children?: readonly unknown[] }[]): string[] {
  return routes.flatMap((route) => [
    ...(route.path ? [route.path] : []),
    ...collectPaths((route.children ?? []) as { path?: string }[]),
  ])
}

describe('AppRoutes', () => {
  beforeEach(() => {
    vi.spyOn(tripApi, 'fetchTrips').mockResolvedValue([])
    vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue({
      id: 1,
      title: '東京五日',
      description: '',
      start_date: '2026-04-01',
      end_date: '2026-04-05',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      role: 'owner',
      days: [],
    })
    vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([])
  })

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

  it('redirects unauthenticated user from /rooms to /login', () => {
    mockAuth(false)
    renderAt('/rooms')
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('redirects authenticated user from / to /rooms', () => {
    mockAuth(true)
    renderAt('/')
    expect(screen.getByTestId('room-list-page')).toBeInTheDocument()
  })

  it('renders room list for authenticated user at /rooms', () => {
    mockAuth(true)
    renderAt('/rooms')
    expect(screen.getByTestId('room-list-page')).toBeInTheDocument()
  })

  it('renders styleguide for authenticated user at /_styleguide', () => {
    mockAuth(true)
    renderAt('/_styleguide')
    expect(screen.getByText(/Travel Chat — Design System/)).toBeInTheDocument()
  })

  it('redirects unauthenticated user from /trips to /login', () => {
    mockAuth(false)
    renderAt('/trips')
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('renders trip list for authenticated user at /trips', () => {
    mockAuth(true)
    renderAt('/trips')
    expect(screen.getByTestId('trip-list-page')).toBeInTheDocument()
  })

  it('renders trip detail for authenticated user at /trips/:id', () => {
    mockAuth(true)
    renderAt('/trips/1')
    expect(screen.getByTestId('trip-detail-page')).toBeInTheDocument()
  })

  it('keeps / redirecting to /rooms rather than /trips', () => {
    mockAuth(true)
    renderAt('/')
    expect(screen.getByTestId('room-list-page')).toBeInTheDocument()
    expect(screen.queryByTestId('trip-list-page')).not.toBeInTheDocument()
  })
})

describe('router (createBrowserRouter definition)', () => {
  it('declares the trip routes alongside the chat routes', () => {
    const paths = collectPaths(router.routes)
    expect(paths).toContain('/trips')
    expect(paths).toContain('/trips/:id')
  })

  it('nests the trip routes under the protected AppShell layout', () => {
    const layout = router.routes.find((route) => !route.path && route.children)
    const childPaths = collectPaths(layout?.children ?? [])
    expect(childPaths).toContain('/trips')
    expect(childPaths).toContain('/trips/:id')
  })
})
