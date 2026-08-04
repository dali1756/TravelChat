import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from '../../src/lib/api'
import * as chatApi from '../../src/lib/chatApi'
import * as tripApi from '../../src/lib/tripApi'
import * as AuthModule from '../../src/auth/AuthContext'
import TripDetailPage from '../../src/pages/TripDetailPage'
import type { Activity, Attraction, TripDay, TripDetail } from '../../src/lib/types'

export function makeAttraction(overrides: Partial<Attraction> = {}): Attraction {
  return {
    id: 9,
    name: '淺草寺',
    address: '東京都台東區',
    latitude: null,
    longitude: null,
    description: '',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

export function mockAuth(userId = 1) {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    currentUser: { id: userId, username: 'jeter', email: 'j@t' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  } as AuthModule.AuthContextValue)
}

export function makeActivity(overrides: Partial<Activity> = {}): Activity {
  return {
    id: 100,
    title: '淺草寺',
    attraction: null,
    start_time: null,
    end_time: null,
    note: '',
    order: 0,
    ...overrides,
  }
}

export function makeDay(overrides: Partial<TripDay> = {}): TripDay {
  return {
    id: 10,
    date: '2026-04-01',
    note: '',
    activities: [],
    ...overrides,
  }
}

export function makeTripDetail(overrides: Partial<TripDetail> = {}): TripDetail {
  return {
    id: 7,
    title: '東京五日',
    description: '賞櫻之旅',
    start_date: '2026-04-01',
    end_date: '2026-04-05',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    role: 'owner',
    days: [],
    ...overrides,
  }
}

export function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/trips/7']}>
      <Routes>
        <Route path="/trips/:id" element={<TripDetailPage />} />
        <Route path="/trips" element={<div data-testid="trip-list-stub" />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('TripDetailPage', () => {
  beforeEach(() => {
    mockAuth()
    vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('mount 時呼叫 GET /api/trips/:id/ 並渲染行程基本資料', async () => {
    const fetchTrip = vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('東京五日')).toBeInTheDocument()
    })
    expect(fetchTrip).toHaveBeenCalledWith(7)
    expect(screen.getByText('賞櫻之旅')).toBeInTheDocument()
    expect(screen.getByText('2026-04-01 ~ 2026-04-05')).toBeInTheDocument()
  })

  it('days 依 date 升冪、activities 依 order 升冪渲染', async () => {
    vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
      makeTripDetail({
        days: [
          makeDay({
            id: 20,
            date: '2026-04-03',
            activities: [
              makeActivity({ id: 201, title: '晚餐', order: 2 }),
              makeActivity({ id: 202, title: '早餐', order: 1 }),
            ],
          }),
          makeDay({ id: 10, date: '2026-04-01', activities: [] }),
        ],
      }),
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getAllByTestId('trip-day')).toHaveLength(2)
    })
    const days = screen.getAllByTestId('trip-day')
    expect(days[0]).toHaveTextContent('2026-04-01')
    expect(days[1]).toHaveTextContent('2026-04-03')

    const activities = within(days[1]).getAllByTestId('activity')
    expect(activities[0]).toHaveTextContent('早餐')
    expect(activities[1]).toHaveTextContent('晚餐')
  })

  it('後端回 404 時顯示無法存取此行程', async () => {
    vi.spyOn(tripApi, 'fetchTrip').mockRejectedValue(new ApiError(404, { detail: 'Not found.' }))

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/無法存取此行程/)).toBeInTheDocument()
    })
  })

  describe('編輯與刪除行程', () => {
    it('owner 編輯標題後 PATCH 並於畫面反映新標題', async () => {
      vi.spyOn(tripApi, 'fetchTrip')
        .mockResolvedValueOnce(makeTripDetail())
        .mockResolvedValueOnce(makeTripDetail({ title: '東京七日' }))
      const updateTrip = vi.spyOn(tripApi, 'updateTrip').mockResolvedValue(
        makeTripDetail({ title: '東京七日' }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '編輯行程' }))
      const titleInput = screen.getByLabelText('標題')
      await user.clear(titleInput)
      await user.type(titleInput, '東京七日')
      await user.click(screen.getByRole('button', { name: '儲存' }))

      await waitFor(() => {
        expect(updateTrip).toHaveBeenCalledWith(7, {
          title: '東京七日',
          description: '賞櫻之旅',
          start_date: '2026-04-01',
          end_date: '2026-04-05',
        })
      })
      expect(await screen.findByText('東京七日')).toBeInTheDocument()
    })

    it('editor 可見編輯入口但不可見刪除入口', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail({ role: 'editor' }))

      renderPage()

      expect(await screen.findByRole('button', { name: '編輯行程' })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: '刪除行程' })).not.toBeInTheDocument()
    })

    it('viewer 不顯示編輯與刪除入口', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail({ role: 'viewer' }))

      renderPage()

      await screen.findByText('東京五日')
      expect(screen.queryByRole('button', { name: '編輯行程' })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: '刪除行程' })).not.toBeInTheDocument()
    })

    it('owner 確認刪除後呼叫 DELETE 並導回 /trips', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      const deleteTrip = vi.spyOn(tripApi, 'deleteTrip').mockResolvedValue(undefined)
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '刪除行程' }))
      await user.click(screen.getByRole('button', { name: '確認刪除' }))

      await waitFor(() => {
        expect(deleteTrip).toHaveBeenCalledWith(7)
      })
      expect(await screen.findByTestId('trip-list-stub')).toBeInTheDocument()
    })

    it('縮小日期範圍導致既有天超出時顯示後端 400 錯誤且不視為成功', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'updateTrip').mockRejectedValue(
        new ApiError(400, {
          non_field_errors: ['行程已有排程日期超出新的日期範圍，請先刪除超出範圍的天。'],
        }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '編輯行程' }))
      fireEvent.change(screen.getByLabelText('結束日期'), { target: { value: '2026-04-02' } })
      await user.click(screen.getByRole('button', { name: '儲存' }))

      expect(
        await screen.findByText(/行程已有排程日期超出新的日期範圍/),
      ).toBeInTheDocument()
      expect(screen.getByLabelText('結束日期')).toBeInTheDocument()
    })
  })

  describe('每日排程管理', () => {
    it('新增一天後 POST 並重取明細以顯示該天', async () => {
      const fetchTrip = vi
        .spyOn(tripApi, 'fetchTrip')
        .mockResolvedValueOnce(makeTripDetail())
        .mockResolvedValueOnce(makeTripDetail({ days: [makeDay({ id: 11, date: '2026-04-02' })] }))
      const createTripDay = vi
        .spyOn(tripApi, 'createTripDay')
        .mockResolvedValue(makeDay({ id: 11, date: '2026-04-02' }))
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '新增一天' }))
      fireEvent.change(screen.getByLabelText('日期'), { target: { value: '2026-04-02' } })
      await user.click(screen.getByRole('button', { name: '新增' }))

      await waitFor(() => {
        expect(createTripDay).toHaveBeenCalledWith(7, { date: '2026-04-02', note: '' })
      })
      await waitFor(() => {
        expect(fetchTrip).toHaveBeenCalledTimes(2)
      })
      expect(await screen.findByText('2026-04-02')).toBeInTheDocument()
    })

    it('日期超出範圍或重複時顯示後端 date 欄位錯誤', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'createTripDay').mockRejectedValue(
        new ApiError(400, { date: ['日期必須在行程起訖範圍內。'] }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '新增一天' }))
      fireEvent.change(screen.getByLabelText('日期'), { target: { value: '2026-05-01' } })
      await user.click(screen.getByRole('button', { name: '新增' }))

      expect(await screen.findByText('日期必須在行程起訖範圍內。')).toBeInTheDocument()
    })

    it('編輯某天的備註時 PATCH 該天', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({ days: [makeDay({ id: 10, date: '2026-04-01' })] }),
      )
      const updateTripDay = vi
        .spyOn(tripApi, 'updateTripDay')
        .mockResolvedValue(makeDay({ id: 10, date: '2026-04-01', note: '市區漫步' }))
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '編輯日期' }))
      await user.type(screen.getByLabelText('備註'), '市區漫步')
      await user.click(screen.getByRole('button', { name: '儲存' }))

      await waitFor(() => {
        expect(updateTripDay).toHaveBeenCalledWith(7, 10, {
          date: '2026-04-01',
          note: '市區漫步',
        })
      })
    })

    it('刪除某天後 DELETE 並重取明細', async () => {
      const fetchTrip = vi
        .spyOn(tripApi, 'fetchTrip')
        .mockResolvedValueOnce(makeTripDetail({ days: [makeDay({ id: 10, date: '2026-04-01' })] }))
        .mockResolvedValueOnce(makeTripDetail({ days: [] }))
      const deleteTripDay = vi.spyOn(tripApi, 'deleteTripDay').mockResolvedValue(undefined)
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '刪除此天' }))
      await user.click(screen.getByRole('button', { name: '確認刪除' }))

      await waitFor(() => {
        expect(deleteTripDay).toHaveBeenCalledWith(7, 10)
      })
      await waitFor(() => {
        expect(fetchTrip).toHaveBeenCalledTimes(2)
      })
      expect(screen.queryAllByTestId('trip-day')).toHaveLength(0)
    })

    it('viewer 不顯示天的寫入入口', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({ role: 'viewer', days: [makeDay({ id: 10, date: '2026-04-01' })] }),
      )

      renderPage()

      const day = (await screen.findAllByTestId('trip-day'))[0]
      expect(screen.queryByRole('button', { name: '新增一天' })).not.toBeInTheDocument()
      expect(within(day).queryByRole('button', { name: '編輯日期' })).not.toBeInTheDocument()
      expect(within(day).queryByRole('button', { name: '刪除此天' })).not.toBeInTheDocument()
    })
  })

  describe('活動管理與排序', () => {
    const dayWithActivities = (activities: Activity[]) =>
      makeTripDetail({ days: [makeDay({ id: 10, date: '2026-04-01', activities })] })

    beforeEach(() => {
      vi.spyOn(tripApi, 'fetchAttractions').mockResolvedValue([])
    })

    it('於某天新增活動時 POST 至該天的 activities 並帶入排序位置', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        dayWithActivities([makeActivity({ id: 201, title: '早餐', order: 0 })]),
      )
      const createActivity = vi
        .spyOn(tripApi, 'createActivity')
        .mockResolvedValue(makeActivity({ id: 202, title: '晚餐', order: 1 }))
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '新增活動' }))
      await user.type(screen.getByLabelText('標題'), '晚餐')
      await user.click(screen.getByRole('button', { name: '新增' }))

      await waitFor(() => {
        expect(createActivity).toHaveBeenCalledWith(7, 10, {
          title: '晚餐',
          attraction_id: null,
          start_time: null,
          end_time: null,
          note: '',
          order: 1,
        })
      })
    })

    it('編輯活動時 PATCH 該活動', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        dayWithActivities([makeActivity({ id: 201, title: '早餐', order: 0 })]),
      )
      const updateActivity = vi
        .spyOn(tripApi, 'updateActivity')
        .mockResolvedValue(makeActivity({ id: 201, title: '早午餐', order: 0 }))
      const user = userEvent.setup()

      renderPage()
      const row = (await screen.findAllByTestId('activity'))[0]
      await user.click(within(row).getByRole('button', { name: '編輯活動' }))
      const titleInput = screen.getByLabelText('標題')
      await user.clear(titleInput)
      await user.type(titleInput, '早午餐')
      await user.click(screen.getByRole('button', { name: '儲存' }))

      await waitFor(() => {
        expect(updateActivity).toHaveBeenCalledWith(7, 10, 201, {
          title: '早午餐',
          attraction_id: null,
          start_time: null,
          end_time: null,
          note: '',
        })
      })
    })

    it('刪除活動時 DELETE 該活動並重取明細', async () => {
      const fetchTrip = vi
        .spyOn(tripApi, 'fetchTrip')
        .mockResolvedValueOnce(dayWithActivities([makeActivity({ id: 201, title: '早餐' })]))
        .mockResolvedValueOnce(dayWithActivities([]))
      const deleteActivity = vi.spyOn(tripApi, 'deleteActivity').mockResolvedValue(undefined)
      const user = userEvent.setup()

      renderPage()
      const row = (await screen.findAllByTestId('activity'))[0]
      await user.click(within(row).getByRole('button', { name: '刪除活動' }))
      await user.click(screen.getByRole('button', { name: '確認刪除' }))

      await waitFor(() => {
        expect(deleteActivity).toHaveBeenCalledWith(7, 10, 201)
      })
      await waitFor(() => {
        expect(fetchTrip).toHaveBeenCalledTimes(2)
      })
    })

    it('下移活動時以 PATCH 交換兩者的 order', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        dayWithActivities([
          makeActivity({ id: 201, title: '早餐', order: 1 }),
          makeActivity({ id: 202, title: '晚餐', order: 2 }),
        ]),
      )
      const updateActivity = vi
        .spyOn(tripApi, 'updateActivity')
        .mockResolvedValue(makeActivity())
      const user = userEvent.setup()

      renderPage()
      const rows = await screen.findAllByTestId('activity')
      await user.click(within(rows[0]).getByRole('button', { name: '下移' }))

      await waitFor(() => {
        expect(updateActivity).toHaveBeenCalledWith(7, 10, 201, { order: 2 })
      })
      expect(updateActivity).toHaveBeenCalledWith(7, 10, 202, { order: 1 })
    })

    it('第一個活動不顯示上移、最後一個不顯示下移', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        dayWithActivities([
          makeActivity({ id: 201, title: '早餐', order: 1 }),
          makeActivity({ id: 202, title: '晚餐', order: 2 }),
        ]),
      )

      renderPage()
      const rows = await screen.findAllByTestId('activity')

      expect(within(rows[0]).queryByRole('button', { name: '上移' })).not.toBeInTheDocument()
      expect(within(rows[0]).getByRole('button', { name: '下移' })).toBeInTheDocument()
      expect(within(rows[1]).getByRole('button', { name: '上移' })).toBeInTheDocument()
      expect(within(rows[1]).queryByRole('button', { name: '下移' })).not.toBeInTheDocument()
    })

    it('結束時間早於開始時間時顯示後端時間欄位錯誤', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(dayWithActivities([]))
      vi.spyOn(tripApi, 'createActivity').mockRejectedValue(
        new ApiError(400, { end_time: ['結束時間不得早於開始時間。'] }),
      )
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '新增活動' }))
      await user.type(screen.getByLabelText('標題'), '晚餐')
      fireEvent.change(screen.getByLabelText('開始時間'), { target: { value: '20:00' } })
      fireEvent.change(screen.getByLabelText('結束時間'), { target: { value: '18:00' } })
      await user.click(screen.getByRole('button', { name: '新增' }))

      expect(await screen.findByText('結束時間不得早於開始時間。')).toBeInTheDocument()
    })

    it('viewer 不顯示活動的寫入與排序入口', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({
          role: 'viewer',
          days: [
            makeDay({
              id: 10,
              date: '2026-04-01',
              activities: [
                makeActivity({ id: 201, title: '早餐', order: 1 }),
                makeActivity({ id: 202, title: '晚餐', order: 2 }),
              ],
            }),
          ],
        }),
      )

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      const rows = within(day).getAllByTestId('activity')

      expect(within(day).queryByRole('button', { name: '新增活動' })).not.toBeInTheDocument()
      expect(within(rows[0]).queryByRole('button', { name: '編輯活動' })).not.toBeInTheDocument()
      expect(within(rows[0]).queryByRole('button', { name: '刪除活動' })).not.toBeInTheDocument()
      expect(within(rows[0]).queryByRole('button', { name: '下移' })).not.toBeInTheDocument()
      expect(within(rows[1]).queryByRole('button', { name: '上移' })).not.toBeInTheDocument()
    })
  })

  describe('景點關聯與即時建立', () => {
    const emptyDay = makeTripDetail({ days: [makeDay({ id: 10, date: '2026-04-01', activities: [] })] })

    it('活動關聯既有景點時帶入 attraction_id', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(emptyDay)
      vi.spyOn(tripApi, 'fetchAttractions').mockResolvedValue([makeAttraction()])
      const createActivity = vi.spyOn(tripApi, 'createActivity').mockResolvedValue(makeActivity())
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '新增活動' }))
      await user.type(screen.getByLabelText('標題'), '參拜')
      await waitFor(() => {
        expect(screen.getByRole('option', { name: '淺草寺' })).toBeInTheDocument()
      })
      await user.selectOptions(screen.getByLabelText('景點'), '9')
      await user.click(screen.getByRole('button', { name: '新增' }))

      await waitFor(() => {
        expect(createActivity).toHaveBeenCalledWith(
          7,
          10,
          expect.objectContaining({ title: '參拜', attraction_id: 9 }),
        )
      })
    })

    it('已關聯景點的活動於明細頁顯示景點資訊', async () => {
      vi.spyOn(tripApi, 'fetchAttractions').mockResolvedValue([])
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({
          days: [
            makeDay({
              id: 10,
              date: '2026-04-01',
              activities: [
                makeActivity({
                  id: 201,
                  title: '參拜',
                  attraction: { id: 9, name: '淺草寺', address: '東京都台東區' },
                }),
              ],
            }),
          ],
        }),
      )

      renderPage()

      const row = (await screen.findAllByTestId('activity'))[0]
      expect(within(row).getByText(/淺草寺/)).toBeInTheDocument()
    })

    it('於選取中即時建立新景點後可立即選用', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(emptyDay)
      vi.spyOn(tripApi, 'fetchAttractions').mockResolvedValue([])
      const createAttraction = vi
        .spyOn(tripApi, 'createAttraction')
        .mockResolvedValue(makeAttraction({ id: 300, name: '晴空塔', address: '' }))
      const createActivity = vi.spyOn(tripApi, 'createActivity').mockResolvedValue(makeActivity())
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '新增活動' }))
      await user.type(screen.getByLabelText('標題'), '登塔')
      await user.type(screen.getByLabelText('新增景點名稱'), '晴空塔')
      await user.click(screen.getByRole('button', { name: '建立景點' }))

      await waitFor(() => {
        expect(createAttraction).toHaveBeenCalledWith({ name: '晴空塔' })
      })
      await waitFor(() => {
        expect(screen.getByLabelText('景點')).toHaveValue('300')
      })

      await user.click(screen.getByRole('button', { name: '新增' }))
      await waitFor(() => {
        expect(createActivity).toHaveBeenCalledWith(
          7,
          10,
          expect.objectContaining({ title: '登塔', attraction_id: 300 }),
        )
      })
    })

    it('僅填標題時建立不關聯景點的純文字活動', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(emptyDay)
      vi.spyOn(tripApi, 'fetchAttractions').mockResolvedValue([makeAttraction()])
      const createActivity = vi.spyOn(tripApi, 'createActivity').mockResolvedValue(makeActivity())
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '新增活動' }))
      await user.type(screen.getByLabelText('標題'), '自由活動')
      await user.click(screen.getByRole('button', { name: '新增' }))

      await waitFor(() => {
        expect(createActivity).toHaveBeenCalledWith(
          7,
          10,
          expect.objectContaining({ title: '自由活動', attraction_id: null }),
        )
      })
    })
  })

  describe('成員分享', () => {
    const member = (overrides = {}) => ({
      id: 1,
      user: { id: 42, username: 'alice' },
      role: 'viewer' as const,
      created_at: '2026-01-01T00:00:00Z',
      ...overrides,
    })

    it('owner 搜尋使用者、指派角色後分享，成員列表顯示 username 與角色', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'fetchTripMembers')
        .mockResolvedValueOnce([])
        .mockResolvedValueOnce([member({ role: 'editor' })])
      const searchUsers = vi
        .spyOn(chatApi, 'searchUsers')
        .mockResolvedValue([{ id: 42, username: 'alice' }])
      const addTripMember = vi
        .spyOn(tripApi, 'addTripMember')
        .mockResolvedValue(member({ role: 'editor' }))
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))
      await user.type(screen.getByLabelText('搜尋使用者'), 'ali')
      await user.click(screen.getByRole('button', { name: '搜尋' }))

      const result = await screen.findByTestId('user-result')
      await user.selectOptions(within(result).getByRole('combobox'), 'editor')
      await user.click(within(result).getByRole('button', { name: '分享' }))

      await waitFor(() => {
        expect(addTripMember).toHaveBeenCalledWith(7, { user_id: 42, role: 'editor' })
      })
      expect(searchUsers).toHaveBeenCalledWith('ali')
      const row = await screen.findByTestId('member-row')
      expect(within(row).getByText('alice')).toBeInTheDocument()
      expect(within(row).getByText('編輯者')).toBeInTheDocument()
    })

    it('分享給已是成員的使用者時顯示後端錯誤且不視為成功', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([])
      vi.spyOn(chatApi, 'searchUsers').mockResolvedValue([{ id: 42, username: 'alice' }])
      vi.spyOn(tripApi, 'addTripMember').mockRejectedValue(
        new ApiError(400, { user_id: ['該使用者已是行程成員。'] }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))
      await user.type(screen.getByLabelText('搜尋使用者'), 'ali')
      await user.click(screen.getByRole('button', { name: '搜尋' }))
      const result = await screen.findByTestId('user-result')
      await user.click(within(result).getByRole('button', { name: '分享' }))

      expect(await screen.findByText('該使用者已是行程成員。')).toBeInTheDocument()
      expect(screen.queryByTestId('member-row')).not.toBeInTheDocument()
    })

    it('owner 移除成員後該成員自列表消失', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'fetchTripMembers')
        .mockResolvedValueOnce([member()])
        .mockResolvedValueOnce([])
      const removeTripMember = vi.spyOn(tripApi, 'removeTripMember').mockResolvedValue(undefined)
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))
      const row = await screen.findByTestId('member-row')
      await user.click(within(row).getByRole('button', { name: '移除' }))

      await waitFor(() => {
        expect(removeTripMember).toHaveBeenCalledWith(7, 42)
      })
      await waitFor(() => {
        expect(screen.queryByTestId('member-row')).not.toBeInTheDocument()
      })
    })

    it('成員自行退出行程後導回 /trips', async () => {
      mockAuth(42)
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail({ role: 'viewer' }))
      vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([member()])
      const removeTripMember = vi.spyOn(tripApi, 'removeTripMember').mockResolvedValue(undefined)
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))
      await user.click(await screen.findByRole('button', { name: '退出行程' }))

      await waitFor(() => {
        expect(removeTripMember).toHaveBeenCalledWith(7, 42)
      })
      expect(await screen.findByTestId('trip-list-stub')).toBeInTheDocument()
    })

    it('非 owner 不顯示邀請與移除他人入口，但可見退出行程', async () => {
      mockAuth(42)
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail({ role: 'editor' }))
      vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([member({ role: 'editor' })])
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))

      const row = await screen.findByTestId('member-row')
      expect(screen.queryByLabelText('搜尋使用者')).not.toBeInTheDocument()
      expect(within(row).queryByRole('button', { name: '移除' })).not.toBeInTheDocument()
      expect(screen.getByRole('button', { name: '退出行程' })).toBeInTheDocument()
    })
  })

  describe('權限拒絕的橫切處理', () => {
    it('編輯行程收到 403 時顯示無權限回饋且不重取明細', async () => {
      const fetchTrip = vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'updateTrip').mockRejectedValue(
        new ApiError(403, { detail: '僅行程擁有者或編輯者可修改行程。' }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '編輯行程' }))
      await user.click(screen.getByRole('button', { name: '儲存' }))

      expect(await screen.findByText('僅行程擁有者或編輯者可修改行程。')).toBeInTheDocument()
      expect(fetchTrip).toHaveBeenCalledTimes(1)
    })

    it('新增活動收到 403 時顯示無權限回饋', async () => {
      vi.spyOn(tripApi, 'fetchAttractions').mockResolvedValue([])
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({ days: [makeDay({ id: 10, date: '2026-04-01', activities: [] })] }),
      )
      vi.spyOn(tripApi, 'createActivity').mockRejectedValue(
        new ApiError(403, { detail: '僅行程擁有者或編輯者可編輯行程內容。' }),
      )
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '新增活動' }))
      await user.type(screen.getByLabelText('標題'), '晚餐')
      await user.click(screen.getByRole('button', { name: '新增' }))

      expect(
        await screen.findByText('僅行程擁有者或編輯者可編輯行程內容。'),
      ).toBeInTheDocument()
    })

    it('刪除天收到 404 時顯示無法存取而非靜默失敗', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({ days: [makeDay({ id: 10, date: '2026-04-01' })] }),
      )
      vi.spyOn(tripApi, 'deleteTripDay').mockRejectedValue(
        new ApiError(404, { detail: 'Not found.' }),
      )
      const user = userEvent.setup()

      renderPage()
      const day = (await screen.findAllByTestId('trip-day'))[0]
      await user.click(within(day).getByRole('button', { name: '刪除此天' }))
      await user.click(screen.getByRole('button', { name: '確認刪除' }))

      expect(await screen.findByText(/無法存取/)).toBeInTheDocument()
      expect(screen.getAllByTestId('trip-day')).toHaveLength(1)
    })

    it('移除成員收到 404 時顯示後端的具體訊息而非通用的無法存取', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([
        {
          id: 1,
          user: { id: 42, username: 'alice' },
          role: 'viewer',
          created_at: '2026-01-01T00:00:00Z',
        },
      ])
      vi.spyOn(tripApi, 'removeTripMember').mockRejectedValue(
        new ApiError(404, { detail: '該使用者不是行程成員。' }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))
      const row = await screen.findByTestId('member-row')
      await user.click(within(row).getByRole('button', { name: '移除' }))

      expect(await screen.findByText('該使用者不是行程成員。')).toBeInTheDocument()
      expect(screen.queryByText(/無法存取此行程/)).not.toBeInTheDocument()
    })

    it('移除成員收到 403 時顯示無權限回饋', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(makeTripDetail())
      vi.spyOn(tripApi, 'fetchTripMembers').mockResolvedValue([
        {
          id: 1,
          user: { id: 42, username: 'alice' },
          role: 'viewer',
          created_at: '2026-01-01T00:00:00Z',
        },
      ])
      vi.spyOn(tripApi, 'removeTripMember').mockRejectedValue(
        new ApiError(403, { detail: '僅行程擁有者可移除成員。' }),
      )
      const user = userEvent.setup()

      renderPage()
      await user.click(await screen.findByRole('button', { name: '成員管理' }))
      const row = await screen.findByTestId('member-row')
      await user.click(within(row).getByRole('button', { name: '移除' }))

      expect(await screen.findByText('僅行程擁有者可移除成員。')).toBeInTheDocument()
    })

    it('調整活動順序收到 403 時於頁面顯示無權限回饋', async () => {
      vi.spyOn(tripApi, 'fetchTrip').mockResolvedValue(
        makeTripDetail({
          days: [
            makeDay({
              id: 10,
              date: '2026-04-01',
              activities: [
                makeActivity({ id: 201, title: '早餐', order: 1 }),
                makeActivity({ id: 202, title: '晚餐', order: 2 }),
              ],
            }),
          ],
        }),
      )
      vi.spyOn(tripApi, 'updateActivity').mockRejectedValue(
        new ApiError(403, { detail: '僅行程擁有者或編輯者可編輯行程內容。' }),
      )
      const user = userEvent.setup()

      renderPage()
      const rows = await screen.findAllByTestId('activity')
      await user.click(within(rows[0]).getByRole('button', { name: '下移' }))

      expect(
        await screen.findByText('僅行程擁有者或編輯者可編輯行程內容。'),
      ).toBeInTheDocument()
    })
  })
})
