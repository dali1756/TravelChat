import { apiFetch } from './api'
import type { Message, Peer, Room } from './types'

export function fetchRooms(): Promise<Room[]> {
  return apiFetch<Room[]>('/api/chats/rooms/')
}

export function fetchMessages(roomId: number): Promise<Message[]> {
  return apiFetch<Message[]>(`/api/chats/rooms/${roomId}/messages/`)
}

export function createDirectRoom(peerUserId: number): Promise<Room> {
  return apiFetch<Room>('/api/chats/rooms/direct/', {
    method: 'POST',
    body: JSON.stringify({ peer_user_id: peerUserId }),
  })
}

export function markRoomRead(roomId: number): Promise<void> {
  return apiFetch<void>(`/api/chats/rooms/${roomId}/read/`, { method: 'POST' })
}

export function searchUsers(q: string): Promise<Peer[]> {
  const params = new URLSearchParams({ q })
  return apiFetch<Peer[]>(`/api/members/search/?${params}`)
}
