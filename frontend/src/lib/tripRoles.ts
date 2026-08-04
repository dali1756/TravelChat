import type { TripRole } from './types'

export const TRIP_ROLE_LABELS: Record<TripRole, string> = {
  owner: '擁有者',
  editor: '編輯者',
  viewer: '檢視者',
}

export function tripRoleLabel(role: TripRole | null | undefined): string {
  return role ? TRIP_ROLE_LABELS[role] : '—'
}
