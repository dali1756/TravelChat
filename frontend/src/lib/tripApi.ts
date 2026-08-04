import { apiFetch } from './api'
import type {
  Activity,
  ActivityInput,
  Attraction,
  AttractionInput,
  Trip,
  TripDay,
  TripDayInput,
  TripDetail,
  TripInput,
  TripMember,
  TripMemberInput,
} from './types'

export function fetchTrips(): Promise<Trip[]> {
  return apiFetch<Trip[]>('/api/trips/')
}

export function fetchTrip(tripId: number): Promise<TripDetail> {
  return apiFetch<TripDetail>(`/api/trips/${tripId}/`)
}

export function createTrip(payload: TripInput): Promise<Trip> {
  return apiFetch<Trip>('/api/trips/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateTrip(tripId: number, payload: Partial<TripInput>): Promise<Trip> {
  return apiFetch<Trip>(`/api/trips/${tripId}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteTrip(tripId: number): Promise<void> {
  return apiFetch<void>(`/api/trips/${tripId}/`, { method: 'DELETE' })
}

export function fetchTripDays(tripId: number): Promise<TripDay[]> {
  return apiFetch<TripDay[]>(`/api/trips/${tripId}/days/`)
}

export function createTripDay(tripId: number, payload: TripDayInput): Promise<TripDay> {
  return apiFetch<TripDay>(`/api/trips/${tripId}/days/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateTripDay(
  tripId: number,
  dayId: number,
  payload: Partial<TripDayInput>,
): Promise<TripDay> {
  return apiFetch<TripDay>(`/api/trips/${tripId}/days/${dayId}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteTripDay(tripId: number, dayId: number): Promise<void> {
  return apiFetch<void>(`/api/trips/${tripId}/days/${dayId}/`, { method: 'DELETE' })
}

export function fetchActivities(tripId: number, dayId: number): Promise<Activity[]> {
  return apiFetch<Activity[]>(`/api/trips/${tripId}/days/${dayId}/activities/`)
}

export function createActivity(
  tripId: number,
  dayId: number,
  payload: ActivityInput,
): Promise<Activity> {
  return apiFetch<Activity>(`/api/trips/${tripId}/days/${dayId}/activities/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateActivity(
  tripId: number,
  dayId: number,
  activityId: number,
  payload: Partial<ActivityInput>,
): Promise<Activity> {
  return apiFetch<Activity>(`/api/trips/${tripId}/days/${dayId}/activities/${activityId}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteActivity(
  tripId: number,
  dayId: number,
  activityId: number,
): Promise<void> {
  return apiFetch<void>(`/api/trips/${tripId}/days/${dayId}/activities/${activityId}/`, {
    method: 'DELETE',
  })
}

export function fetchAttractions(): Promise<Attraction[]> {
  return apiFetch<Attraction[]>('/api/trips/attractions/')
}

export function createAttraction(payload: AttractionInput): Promise<Attraction> {
  return apiFetch<Attraction>('/api/trips/attractions/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchTripMembers(tripId: number): Promise<TripMember[]> {
  return apiFetch<TripMember[]>(`/api/trips/${tripId}/members/`)
}

export function addTripMember(tripId: number, payload: TripMemberInput): Promise<TripMember> {
  return apiFetch<TripMember>(`/api/trips/${tripId}/members/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function removeTripMember(tripId: number, userId: number): Promise<void> {
  return apiFetch<void>(`/api/trips/${tripId}/members/${userId}/`, { method: 'DELETE' })
}
