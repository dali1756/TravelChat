export interface Peer {
  id: number
  username: string
}

export interface LastMessage {
  id: number
  content: string
  sender_username: string
  created_at: string
}

export interface Room {
  id: number
  room_type: string
  peer: Peer | null
  last_message: LastMessage | null
  last_message_at: string | null
  created_at: string
  unread_count: number
}

export interface Message {
  id: number
  sender_id: number
  sender_username: string
  message_type: string
  content: string
  created_at: string
}
