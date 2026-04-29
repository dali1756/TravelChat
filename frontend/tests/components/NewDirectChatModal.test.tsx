import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import * as chatApi from '../../src/lib/chatApi'
import NewDirectChatModal from '../../src/components/NewDirectChatModal'

function renderModal(onRoomSelected = vi.fn()) {
  return render(
    <MemoryRouter>
      <NewDirectChatModal show onHide={vi.fn()} onRoomSelected={onRoomSelected} />
    </MemoryRouter>,
  )
}

describe('NewDirectChatModal', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows search results when user types a query', async () => {
    vi.spyOn(chatApi, 'searchUsers').mockResolvedValue([
      { id: 2, username: 'alice' },
      { id: 3, username: 'alicia' },
    ])

    renderModal()

    await userEvent.type(screen.getByPlaceholderText(/搜尋使用者名稱/), 'ali')

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
      expect(screen.getByText('alicia')).toBeInTheDocument()
    })
  })

  it('shows empty state when no users found', async () => {
    vi.spyOn(chatApi, 'searchUsers').mockResolvedValue([])

    renderModal()

    await userEvent.type(screen.getByPlaceholderText(/搜尋使用者名稱/), 'xyz')

    await waitFor(() => {
      expect(screen.getByText(/找不到符合的使用者/)).toBeInTheDocument()
    })
  })

  it('calls onRoomSelected with room id after selecting a user', async () => {
    vi.spyOn(chatApi, 'searchUsers').mockResolvedValue([{ id: 2, username: 'alice' }])
    vi.spyOn(chatApi, 'createDirectRoom').mockResolvedValue({
      id: 42,
      room_type: 'direct',
      peer: { id: 2, username: 'alice' },
      last_message: null,
      last_message_at: null,
      created_at: '2024-01-01T00:00:00Z',
      unread_count: 0,
    })
    const onRoomSelected = vi.fn()

    renderModal(onRoomSelected)

    await userEvent.type(screen.getByPlaceholderText(/搜尋使用者名稱/), 'ali')
    await waitFor(() => screen.getByText('alice'))
    await userEvent.click(screen.getByText('alice'))

    await waitFor(() => {
      expect(onRoomSelected).toHaveBeenCalledWith(42)
    })
  })
})
