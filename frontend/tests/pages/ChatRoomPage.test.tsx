import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import * as chatApi from '../../src/lib/chatApi'
import * as AuthModule from '../../src/auth/AuthContext'
import ChatRoomPage from '../../src/pages/ChatRoomPage'

// jsdom does not implement scrollIntoView
HTMLElement.prototype.scrollIntoView = vi.fn()

class MockWebSocket {
  static instances: MockWebSocket[] = []
  onmessage: ((e: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null

  constructor(public url: string) {
    MockWebSocket.instances.push(this)
  }

  send(_data: string) {}
  close() {}
}

function mockAuth(userId = 1) {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: { id: userId, username: 'me', email: 'me@t' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  } as AuthModule.AuthContextValue)
}

function renderChatRoom(roomId = 1) {
  return render(
    <MemoryRouter initialEntries={[`/rooms/${roomId}`]}>
      <Routes>
        <Route path="/rooms/:id" element={<ChatRoomPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

async function waitForWs(): Promise<MockWebSocket> {
  // After loading finishes, the WS connection effect fires.
  // Wait until an instance appears.
  await waitFor(() => {
    expect(MockWebSocket.instances.length).toBeGreaterThan(0)
  })
  return MockWebSocket.instances[MockWebSocket.instances.length - 1]
}

describe('ChatRoomPage — mark-read behaviour', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.restoreAllMocks()
    mockAuth(1)
    vi.spyOn(chatApi, 'fetchMessages').mockResolvedValue([])
  })

  it('calls markRoomRead once on mount', async () => {
    const markRead = vi.spyOn(chatApi, 'markRoomRead').mockResolvedValue(undefined)

    renderChatRoom(1)

    await waitFor(() => {
      expect(markRead).toHaveBeenCalledTimes(1)
      expect(markRead).toHaveBeenCalledWith(1)
    })
  })

  it('calls markRoomRead again when receiving a message from another user', async () => {
    const markRead = vi.spyOn(chatApi, 'markRoomRead').mockResolvedValue(undefined)

    renderChatRoom(1)

    // Wait for mount mark-read AND WS to be created
    await waitFor(() => expect(markRead).toHaveBeenCalledTimes(1))
    const ws = await waitForWs()

    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'message.new',
          message: {
            id: 99,
            sender_id: 2,
            sender_username: 'alice',
            message_type: 'text',
            content: 'hi',
            created_at: '2024-01-01T00:00:00Z',
          },
        }),
      })
    })

    await waitFor(() => {
      expect(markRead).toHaveBeenCalledTimes(2)
    })
  })

  it('does NOT call markRoomRead for own messages', async () => {
    const markRead = vi.spyOn(chatApi, 'markRoomRead').mockResolvedValue(undefined)

    renderChatRoom(1)

    await waitFor(() => expect(markRead).toHaveBeenCalledTimes(1))
    const ws = await waitForWs()

    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'message.new',
          message: {
            id: 100,
            sender_id: 1,
            sender_username: 'me',
            message_type: 'text',
            content: 'my message',
            created_at: '2024-01-01T00:00:00Z',
          },
        }),
      })
    })

    // Give enough time for any spurious calls
    await new Promise((r) => setTimeout(r, 50))
    expect(markRead).toHaveBeenCalledTimes(1)
  })

  it('shows access error when backend returns 403', async () => {
    const { ApiError } = await import('../../src/lib/api')
    vi.spyOn(chatApi, 'fetchMessages').mockRejectedValue(new ApiError(403, {}))
    vi.spyOn(chatApi, 'markRoomRead').mockResolvedValue(undefined)

    renderChatRoom(1)

    await waitFor(() => {
      expect(screen.getByText(/無法存取此聊天室/)).toBeInTheDocument()
    })
  })
})
