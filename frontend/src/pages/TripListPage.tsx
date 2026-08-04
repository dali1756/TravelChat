import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Alert from 'react-bootstrap/Alert'
import Badge from 'react-bootstrap/Badge'
import Button from 'react-bootstrap/Button'
import Container from 'react-bootstrap/Container'
import ListGroup from 'react-bootstrap/ListGroup'
import Spinner from 'react-bootstrap/Spinner'
import TripFormModal from '../components/TripFormModal'
import { createTrip, fetchTrips } from '../lib/tripApi'
import { tripRoleLabel } from '../lib/tripRoles'
import type { Trip, TripInput } from '../lib/types'

export default function TripListPage() {
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchTrips().then(setTrips).catch(
      () => setError('載入行程失敗，請重新整理。')
    ).finally(
      () => setLoading(false)
    )
  }, [])

  return (
    <Container className="py-4" data-testid="trip-list-page">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="mb-0">我的行程</h5>
        <Button size="sm" onClick={() => setShowCreate(true)}>建立行程</Button>
      </div>

      {loading && <Spinner animation="border" size="sm" />}
      {error && <Alert variant="danger">{error}</Alert>}

      {!loading && !error && trips.length === 0 && (
        <p className="text-muted">尚無行程，點擊建立開始規劃。</p>
      )}

      {!loading && !error && trips.length > 0 && (
        <ListGroup>
          {trips.map((trip) => (
            <ListGroup.Item key={trip.id} action className="d-flex justify-content-between align-items-center" onClick={() => navigate(`/trips/${trip.id}`)}>
              <div>
                <div className="fw-semibold">{trip.title}</div>
                <small className="text-muted">
                  {trip.start_date} ~ {trip.end_date}
                </small>
              </div>
              <Badge bg="secondary" data-testid={`trip-role-${trip.id}`}>{tripRoleLabel(trip.role)}</Badge>
            </ListGroup.Item>
          ))}
        </ListGroup>
      )}

      <TripFormModal
        show={showCreate}
        heading="建立行程"
        submitLabel="建立"
        onHide={() => setShowCreate(false)}
        onSubmit={async (payload: TripInput) => {
          const trip = await createTrip(payload)
          setShowCreate(false)
          navigate(`/trips/${trip.id}`)
        }}
      />
    </Container>
  )
}
