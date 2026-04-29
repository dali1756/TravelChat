import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import * as chatApi from '../../src/lib/chatApi'
import * as AuthModule from '../../src/auth/AuthContext'
import RoomListPage from '../../src/pages/RoomListPage'
import type { Room } from '../../src/lib/types'

function mockAuth() {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: { id: 1, username: 'jeter', email: 'j@t' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  } as AuthModule.AuthContextValue)
}

function makeRoom(overrides: Partial<Room> = {}): Room {
  return {
    id: 1,
    room_type: 'direct',
    peer: { id: 2, username: 'alice' },
    last_message: { id: 10, content: 'Hello!', sender_username: 'alice', created_at: '2024-01-01T00:00:00Z' },
    last_message_at: '2024-01-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    unread_count: 0,
    ...overrides,
  }
}

function renderPage() {
  return render(
    <MemoryRouter>
      <RoomListPage />
    </MemoryRouter>,
  )
}

describe('RoomListPage', () => {
  beforeEach(() => {
    mockAuth()
  })

  it('renders room list with peer username and last message', async () => {
    vi.spyOn(chatApi, 'fetchRooms').mockResolvedValue([makeRoom()])

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
      expect(screen.getByText('Hello!')).toBeInTheDocument()
    })
  })

  it('shows empty state when no rooms', async () => {
    vi.spyOn(chatApi, 'fetchRooms').mockResolvedValue([])

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/尚無對話/)).toBeInTheDocument()
    })
  })

  it('shows unread badge when unread_count > 0', async () => {
    vi.spyOn(chatApi, 'fetchRooms').mockResolvedValue([makeRoom({ unread_count: 3 })])

    renderPage()

    await waitFor(() => {
      expect(screen.getByTestId('unread-badge')).toBeInTheDocument()
      expect(screen.getByTestId('unread-badge')).toHaveTextContent('3')
    })
  })

  it('hides unread badge when unread_count is 0', async () => {
    vi.spyOn(chatApi, 'fetchRooms').mockResolvedValue([makeRoom({ unread_count: 0 })])

    renderPage()

    await waitFor(() => {
      expect(screen.queryByTestId('unread-badge')).not.toBeInTheDocument()
    })
  })

  it('shows error message on fetch failure', async () => {
    vi.spyOn(chatApi, 'fetchRooms').mockRejectedValue(new Error('network error'))

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/載入聊天室失敗/)).toBeInTheDocument()
    })
  })
})
