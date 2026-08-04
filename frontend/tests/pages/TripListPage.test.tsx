import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from '../../src/lib/api'
import * as tripApi from '../../src/lib/tripApi'
import TripListPage from '../../src/pages/TripListPage'
import type { Trip } from '../../src/lib/types'

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: 1,
    title: '東京五日',
    description: '賞櫻',
    start_date: '2026-04-01',
    end_date: '2026-04-05',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    role: 'owner',
    ...overrides,
  }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/trips']}>
      <Routes>
        <Route path="/trips" element={<TripListPage />} />
        <Route path="/trips/:id" element={<div data-testid="trip-detail-stub" />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('TripListPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('載入與顯示', () => {
    beforeEach(() => {
      vi.spyOn(tripApi, 'createTrip').mockResolvedValue(makeTrip())
    })

    it('mount 時呼叫 GET /api/trips/ 並渲染標題、起訖日期與角色', async () => {
      const fetchTrips = vi.spyOn(tripApi, 'fetchTrips').mockResolvedValue([makeTrip()])

      renderPage()

      await waitFor(() => {
        expect(screen.getByText('東京五日')).toBeInTheDocument()
      })
      expect(fetchTrips).toHaveBeenCalledTimes(1)
      expect(screen.getByText('2026-04-01 ~ 2026-04-05')).toBeInTheDocument()
      expect(screen.getByTestId('trip-role-1')).toHaveTextContent('擁有者')
    })

    it('依角色顯示 editor 與 viewer 標示', async () => {
      vi.spyOn(tripApi, 'fetchTrips').mockResolvedValue([
        makeTrip({ id: 1, title: '大阪行', role: 'editor' }),
        makeTrip({ id: 2, title: '京都行', role: 'viewer' }),
      ])

      renderPage()

      await waitFor(() => {
        expect(screen.getByTestId('trip-role-1')).toHaveTextContent('編輯者')
      })
      expect(screen.getByTestId('trip-role-2')).toHaveTextContent('檢視者')
    })

    it('無行程時顯示空狀態，且仍顯示建立入口', async () => {
      vi.spyOn(tripApi, 'fetchTrips').mockResolvedValue([])

      renderPage()

      await waitFor(() => {
        expect(screen.getByText(/尚無行程/)).toBeInTheDocument()
      })
      expect(screen.getByRole('button', { name: '建立行程' })).toBeInTheDocument()
    })

    it('載入失敗時顯示錯誤訊息', async () => {
      vi.spyOn(tripApi, 'fetchTrips').mockRejectedValue(new Error('network error'))

      renderPage()

      await waitFor(() => {
        expect(screen.getByText(/載入行程失敗/)).toBeInTheDocument()
      })
    })
  })

  describe('建立行程', () => {
    beforeEach(() => {
      vi.spyOn(tripApi, 'fetchTrips').mockResolvedValue([])
    })

    async function openFormAndFill() {
      const user = userEvent.setup()
      renderPage()
      await user.click(await screen.findByRole('button', { name: '建立行程' }))
      await user.type(screen.getByLabelText('標題'), '東京五日')
      fireEvent.change(screen.getByLabelText('起始日期'), { target: { value: '2026-04-01' } })
      fireEvent.change(screen.getByLabelText('結束日期'), { target: { value: '2026-04-05' } })
      return user
    }

    it('提交合法資料時呼叫 POST /api/trips/ 並導向新行程明細頁', async () => {
      const createTrip = vi.spyOn(tripApi, 'createTrip').mockResolvedValue(makeTrip({ id: 42 }))

      const user = await openFormAndFill()
      await user.click(screen.getByRole('button', { name: '建立' }))

      await waitFor(() => {
        expect(createTrip).toHaveBeenCalledWith({
          title: '東京五日',
          description: '',
          start_date: '2026-04-01',
          end_date: '2026-04-05',
        })
      })
      expect(await screen.findByTestId('trip-detail-stub')).toBeInTheDocument()
    })

    it('後端回 400 時顯示欄位錯誤且不導頁', async () => {
      vi.spyOn(tripApi, 'createTrip').mockRejectedValue(
        new ApiError(400, { end_date: ['結束日期不得早於起始日期。'] }),
      )

      const user = await openFormAndFill()
      await user.click(screen.getByRole('button', { name: '建立' }))

      expect(await screen.findByText('結束日期不得早於起始日期。')).toBeInTheDocument()
      expect(screen.queryByTestId('trip-detail-stub')).not.toBeInTheDocument()
    })
  })
})
