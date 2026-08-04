import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import Card from 'react-bootstrap/Card'
import Container from 'react-bootstrap/Container'
import ListGroup from 'react-bootstrap/ListGroup'
import Spinner from 'react-bootstrap/Spinner'
import Stack from 'react-bootstrap/Stack'
import ActivityFormModal from '../components/ActivityFormModal'
import { toFormValues } from '../lib/activityForm'
import ConfirmModal from '../components/ConfirmModal'
import TripDayFormModal from '../components/TripDayFormModal'
import TripFormModal from '../components/TripFormModal'
import TripMembersModal from '../components/TripMembersModal'
import { useAuth } from '../auth/AuthContext'
import { accessErrorMessage } from '../lib/formErrors'
import {
  createActivity,
  createTripDay,
  deleteActivity,
  deleteTrip,
  deleteTripDay,
  fetchTrip,
  updateActivity,
  updateTrip,
  updateTripDay,
} from '../lib/tripApi'
import type { Activity, TripDay, TripDetail } from '../lib/types'

function sortedDays(trip: TripDetail | null): TripDay[] {
  return [...(trip?.days ?? [])].sort((a, b) => a.date.localeCompare(b.date))
}

function sortedActivities(day: TripDay): Activity[] {
  return [...(day.activities ?? [])].sort((a, b) => a.order - b.order || a.id - b.id)
}

interface ActivityFormState {
  day: TripDay
  activity: Activity | null
}

export default function TripDetailPage() {
  const { id } = useParams()
  const tripId = Number(id)
  const [trip, setTrip] = useState<TripDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [showEditTrip, setShowEditTrip] = useState(false)
  const [showDeleteTrip, setShowDeleteTrip] = useState(false)
  const [dayForm, setDayForm] = useState<{ day: TripDay | null } | null>(null)
  const [deletingDay, setDeletingDay] = useState<TripDay | null>(null)
  const [activityForm, setActivityForm] = useState<ActivityFormState | null>(null)
  const [deletingActivity, setDeletingActivity] = useState<ActivityFormState | null>(null)
  const [showMembers, setShowMembers] = useState(false)
  const { currentUser } = useAuth()
  const navigate = useNavigate()

  const reloadTrip = useCallback(() => fetchTrip(tripId).then(setTrip), [tripId])

  useEffect(() => {
    reloadTrip()
      .catch((err) => setError(accessErrorMessage(err, '載入行程失敗，請重新整理。')))
      .finally(() => setLoading(false))
  }, [reloadTrip])

  const days = useMemo(() => sortedDays(trip), [trip])
  const isOwner = trip?.role === 'owner'
  const canEdit = isOwner || trip?.role === 'editor'

  async function moveActivity(day: TripDay, ordered: Activity[], index: number, delta: number) {
    const current = ordered[index]
    const neighbor = ordered[index + delta]
    if (!neighbor) return
    setActionError(null)
    try {
      await updateActivity(tripId, day.id, current.id, { order: neighbor.order })
      await updateActivity(tripId, day.id, neighbor.id, { order: current.order })
      await reloadTrip()
    } catch (err) {
      setActionError(accessErrorMessage(err, '調整活動順序失敗，請稍後再試。'))
    }
  }

  if (loading) {
    return (
      <Container className="py-4" data-testid="trip-detail-page">
        <Spinner animation="border" size="sm" />
      </Container>
    )
  }

  if (error || !trip) {
    return (
      <Container className="py-4" data-testid="trip-detail-page">
        <Alert variant="danger">{error ?? '無法存取此行程。'}</Alert>
      </Container>
    )
  }

  return (
    <Container className="py-4" data-testid="trip-detail-page">
      {actionError && (
        <Alert variant="danger" dismissible onClose={() => setActionError(null)}>
          {actionError}
        </Alert>
      )}

      <Card className="mb-4">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start gap-3">
            <div>
              <h5 className="mb-1">{trip.title}</h5>
              <div className="text-muted small mb-2">
                {trip.start_date} ~ {trip.end_date}
              </div>
              {trip.description && <p className="mb-0">{trip.description}</p>}
            </div>
            <Stack direction="horizontal" gap={2}>
              <Button size="sm" variant="outline-secondary" onClick={() => setShowMembers(true)}>成員管理</Button>
              {canEdit && (
                <Button size="sm" variant="outline-primary" onClick={() => setShowEditTrip(true)}>編輯行程</Button>
              )}
              {isOwner && (
                <Button size="sm" variant="outline-danger" onClick={() => setShowDeleteTrip(true)}>刪除行程</Button>
              )}
            </Stack>
          </div>
        </Card.Body>
      </Card>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="mb-0">每日排程</h6>
        {canEdit && (
          <Button size="sm" variant="outline-primary" onClick={() => setDayForm({ day: null })}>新增一天</Button>
        )}
      </div>

      <Stack gap={3}>
        {days.length === 0 && <p className="text-muted">尚無排程日期。</p>}
        {days.map((day) => {
          const activities = sortedActivities(day)
          return (
            <Card key={day.id} data-testid="trip-day">
              <Card.Header className="d-flex justify-content-between align-items-center">
                <div>
                  <span className="fw-semibold">{day.date}</span>
                  {day.note && <div className="text-muted small">{day.note}</div>}
                </div>
                {canEdit && (
                  <Stack direction="horizontal" gap={2}>
                    <Button size="sm" variant="outline-secondary" onClick={() => setDayForm({ day })}>編輯日期</Button>
                    <Button size="sm" variant="outline-danger" onClick={() => setDeletingDay(day)}>刪除此天</Button>
                  </Stack>
                )}
              </Card.Header>
              <ListGroup variant="flush">
                {activities.length === 0 && (
                  <ListGroup.Item className="text-muted">尚無活動。</ListGroup.Item>
                )}
                {activities.map((activity, index) => (
                  <ListGroup.Item key={activity.id} data-testid="activity" className="d-flex justify-content-between align-items-start gap-3">
                    <div>
                      <span className="fw-semibold">{activity.title}</span>
                      {activity.attraction && (
                        <div className="text-muted small">
                          景點 · {activity.attraction.name}
                          {activity.attraction.address ? `（${activity.attraction.address}）` : ''}
                        </div>
                      )}
                      {(activity.start_time || activity.end_time) && (
                        <div className="text-muted small">
                          {activity.start_time ?? '—'} ~ {activity.end_time ?? '—'}
                        </div>
                      )}
                      {activity.note && <div className="text-muted small">{activity.note}</div>}
                    </div>
                    {canEdit && (
                      <Stack direction="horizontal" gap={2}>
                        {index > 0 && (
                          <Button size="sm" variant="outline-secondary" onClick={() => moveActivity(day, activities, index, -1)}>上移</Button>
                        )}
                        {index < activities.length - 1 && (
                          <Button size="sm" variant="outline-secondary" onClick={() => moveActivity(day, activities, index, 1)}>下移</Button>
                        )}
                        <Button size="sm" variant="outline-secondary" onClick={() => setActivityForm({ day, activity })}>編輯活動</Button>
                        <Button size="sm" variant="outline-danger" onClick={() => setDeletingActivity({ day, activity })}>刪除活動</Button>
                      </Stack>
                    )}
                  </ListGroup.Item>
                ))}
                {canEdit && (
                  <ListGroup.Item>
                    <Button size="sm" variant="outline-primary" onClick={() => setActivityForm({ day, activity: null })}>新增活動</Button>
                  </ListGroup.Item>
                )}
              </ListGroup>
            </Card>
          )
        })}
      </Stack>

      <TripFormModal
        show={showEditTrip}
        heading="編輯行程"
        submitLabel="儲存"
        initial={{
          title: trip.title,
          description: trip.description,
          start_date: trip.start_date,
          end_date: trip.end_date,
        }}
        onHide={() => setShowEditTrip(false)}
        onSubmit={async (payload) => {
          await updateTrip(tripId, payload)
          await reloadTrip()
          setShowEditTrip(false)
        }}
      />

      <TripDayFormModal
        show={dayForm !== null}
        heading={dayForm?.day ? '編輯排程日期' : '新增排程日期'}
        submitLabel={dayForm?.day ? '儲存' : '新增'}
        initial={dayForm?.day ? { date: dayForm.day.date, note: dayForm.day.note } : undefined}
        onHide={() => setDayForm(null)}
        onSubmit={async (payload) => {
          if (dayForm?.day) {
            await updateTripDay(tripId, dayForm.day.id, payload)
          } else {
            await createTripDay(tripId, payload)
          }
          await reloadTrip()
          setDayForm(null)
        }}
      />

      <ActivityFormModal
        show={activityForm !== null}
        heading={activityForm?.activity ? '編輯活動' : '新增活動'}
        submitLabel={activityForm?.activity ? '儲存' : '新增'}
        initial={toFormValues(activityForm?.activity ?? null)}
        onHide={() => setActivityForm(null)}
        onSubmit={async (payload) => {
          if (!activityForm) return
          const { day, activity } = activityForm
          if (activity) {
            await updateActivity(tripId, day.id, activity.id, payload)
          } else {
            await createActivity(tripId, day.id, {
              ...payload,
              order: (day.activities ?? []).length,
            })
          }
          await reloadTrip()
          setActivityForm(null)
        }}
      />

      <ConfirmModal
        show={deletingActivity !== null}
        heading="刪除活動"
        body={`確定要刪除「${deletingActivity?.activity?.title ?? ''}」嗎？`}
        confirmLabel="確認刪除"
        onHide={() => setDeletingActivity(null)}
        onConfirm={async () => {
          if (!deletingActivity?.activity) return
          await deleteActivity(tripId, deletingActivity.day.id, deletingActivity.activity.id)
          await reloadTrip()
          setDeletingActivity(null)
        }}
      />

      <ConfirmModal
        show={deletingDay !== null}
        heading="刪除排程日期"
        body={`刪除 ${deletingDay?.date ?? ''} 將一併移除當天所有活動，確定要刪除嗎？`}
        confirmLabel="確認刪除"
        onHide={() => setDeletingDay(null)}
        onConfirm={async () => {
          if (!deletingDay) return
          await deleteTripDay(tripId, deletingDay.id)
          await reloadTrip()
          setDeletingDay(null)
        }}
      />

      <TripMembersModal
        show={showMembers}
        tripId={tripId}
        isOwner={!!isOwner}
        currentUserId={currentUser?.id ?? null}
        onHide={() => setShowMembers(false)}
        onLeft={() => {
          setShowMembers(false)
          navigate('/trips', { replace: true })
        }}
      />

      <ConfirmModal
        show={showDeleteTrip}
        heading="刪除行程"
        body="刪除後將一併移除所有排程與活動，且無法復原。確定要刪除嗎？"
        confirmLabel="確認刪除"
        onHide={() => setShowDeleteTrip(false)}
        onConfirm={async () => {
          await deleteTrip(tripId)
          navigate('/trips', { replace: true })
        }}
      />
    </Container>
  )
}
