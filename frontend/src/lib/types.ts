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

export type TripRole = 'owner' | 'editor' | 'viewer'

export type TripMemberRole = 'editor' | 'viewer'

export interface AttractionSummary {
  id: number
  name: string
  address: string
}

export interface Attraction extends AttractionSummary {
  latitude: string | null
  longitude: string | null
  description: string
  created_at: string
}

export interface Activity {
  id: number
  day?: number
  title: string
  attraction: AttractionSummary | null
  start_time: string | null
  end_time: string | null
  note: string
  order: number
}

export interface TripDay {
  id: number
  date: string
  note: string
  activities?: Activity[]
}

export interface TripMember {
  id: number
  user: Peer
  role: TripMemberRole
  created_at: string
}

export interface Trip {
  id: number
  title: string
  description: string
  start_date: string
  end_date: string
  created_at: string
  updated_at: string
  role: TripRole | null
}

export interface TripDetail extends Trip {
  days: TripDay[]
}

export interface TripInput {
  title: string
  description?: string
  start_date: string
  end_date: string
}

export interface TripDayInput {
  date: string
  note?: string
}

export interface ActivityInput {
  title: string
  attraction_id?: number | null
  start_time?: string | null
  end_time?: string | null
  note?: string
  order?: number
}

export interface AttractionInput {
  name: string
  address?: string
  description?: string
}

export interface TripMemberInput {
  user_id: number
  role: TripMemberRole
}
