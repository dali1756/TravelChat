import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as api from '../../src/lib/api'
import * as tripApi from '../../src/lib/tripApi'

function spyApiFetch() {
  return vi.spyOn(api, 'apiFetch').mockResolvedValue(undefined as never)
}

describe('tripApi', () => {
  let apiFetch: ReturnType<typeof spyApiFetch>

  beforeEach(() => {
    apiFetch = spyApiFetch()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('trips', () => {
    it('fetchTrips calls GET /api/trips/', async () => {
      await tripApi.fetchTrips()
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/')
    })

    it('fetchTrip calls GET /api/trips/:id/', async () => {
      await tripApi.fetchTrip(7)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/')
    })

    it('createTrip POSTs the trip payload', async () => {
      await tripApi.createTrip({
        title: '東京五日',
        description: '賞櫻',
        start_date: '2026-04-01',
        end_date: '2026-04-05',
      })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/', {
        method: 'POST',
        body: JSON.stringify({
          title: '東京五日',
          description: '賞櫻',
          start_date: '2026-04-01',
          end_date: '2026-04-05',
        }),
      })
    })

    it('updateTrip PATCHes only the given fields', async () => {
      await tripApi.updateTrip(7, { title: '改名' })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/', {
        method: 'PATCH',
        body: JSON.stringify({ title: '改名' }),
      })
    })

    it('deleteTrip calls DELETE /api/trips/:id/', async () => {
      await tripApi.deleteTrip(7)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/', { method: 'DELETE' })
    })
  })

  describe('days', () => {
    it('fetchTripDays calls GET /api/trips/:id/days/', async () => {
      await tripApi.fetchTripDays(7)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/')
    })

    it('createTripDay POSTs to the trip days collection', async () => {
      await tripApi.createTripDay(7, { date: '2026-04-02', note: '市區' })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/', {
        method: 'POST',
        body: JSON.stringify({ date: '2026-04-02', note: '市區' }),
      })
    })

    it('updateTripDay PATCHes the day', async () => {
      await tripApi.updateTripDay(7, 3, { note: '改備註' })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/3/', {
        method: 'PATCH',
        body: JSON.stringify({ note: '改備註' }),
      })
    })

    it('deleteTripDay calls DELETE on the day', async () => {
      await tripApi.deleteTripDay(7, 3)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/3/', { method: 'DELETE' })
    })
  })

  describe('activities', () => {
    it('fetchActivities calls GET on the day activities collection', async () => {
      await tripApi.fetchActivities(7, 3)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/3/activities/')
    })

    it('createActivity POSTs to the day activities collection', async () => {
      await tripApi.createActivity(7, 3, { title: '淺草寺', attraction_id: 9 })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/3/activities/', {
        method: 'POST',
        body: JSON.stringify({ title: '淺草寺', attraction_id: 9 }),
      })
    })

    it('updateActivity PATCHes the activity', async () => {
      await tripApi.updateActivity(7, 3, 12, { order: 1 })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/3/activities/12/', {
        method: 'PATCH',
        body: JSON.stringify({ order: 1 }),
      })
    })

    it('deleteActivity calls DELETE on the activity', async () => {
      await tripApi.deleteActivity(7, 3, 12)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/days/3/activities/12/', {
        method: 'DELETE',
      })
    })
  })

  describe('attractions', () => {
    it('fetchAttractions calls GET /api/trips/attractions/', async () => {
      await tripApi.fetchAttractions()
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/attractions/')
    })

    it('createAttraction POSTs the attraction payload', async () => {
      await tripApi.createAttraction({ name: '晴空塔', address: '押上' })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/attractions/', {
        method: 'POST',
        body: JSON.stringify({ name: '晴空塔', address: '押上' }),
      })
    })
  })

  describe('members', () => {
    it('fetchTripMembers calls GET /api/trips/:id/members/', async () => {
      await tripApi.fetchTripMembers(7)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/members/')
    })

    it('addTripMember POSTs user_id and role', async () => {
      await tripApi.addTripMember(7, { user_id: 42, role: 'editor' })
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/members/', {
        method: 'POST',
        body: JSON.stringify({ user_id: 42, role: 'editor' }),
      })
    })

    it('removeTripMember calls DELETE /api/trips/:id/members/:userId/', async () => {
      await tripApi.removeTripMember(7, 42)
      expect(apiFetch).toHaveBeenCalledWith('/api/trips/7/members/42/', { method: 'DELETE' })
    })
  })
})
