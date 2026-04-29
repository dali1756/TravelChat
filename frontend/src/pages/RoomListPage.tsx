import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import ListGroup from 'react-bootstrap/ListGroup'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import Alert from 'react-bootstrap/Alert'
import { fetchRooms } from '../lib/chatApi'
import type { Room } from '../lib/types'
import UnreadBadge from '../components/UnreadBadge'
import NewDirectChatModal from '../components/NewDirectChatModal'

export default function RoomListPage() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchRooms()
      .then(setRooms)
      .catch(() => setError('載入聊天室失敗，請重新整理。'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Container className="py-4" data-testid="room-list-page">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="mb-0">對話列表</h5>
        <Button size="sm" onClick={() => setShowModal(true)}>
          新增對話
        </Button>
      </div>

      {loading && <Spinner animation="border" size="sm" />}
      {error && <Alert variant="danger">{error}</Alert>}

      {!loading && !error && rooms.length === 0 && (
        <p className="text-muted">尚無對話，點擊新增開始聊天。</p>
      )}

      {!loading && !error && rooms.length > 0 && (
        <ListGroup>
          {rooms.map((room) => (
            <ListGroup.Item
              key={room.id}
              action
              className="d-flex justify-content-between align-items-center"
              onClick={() => navigate(`/rooms/${room.id}`)}
            >
              <div>
                <div className="fw-semibold">{room.peer?.username ?? '未知使用者'}</div>
                {room.last_message && (
                  <small className="text-muted">{room.last_message.content}</small>
                )}
              </div>
              <UnreadBadge count={room.unread_count} />
            </ListGroup.Item>
          ))}
        </ListGroup>
      )}

      <NewDirectChatModal
        show={showModal}
        onHide={() => setShowModal(false)}
        onRoomSelected={(id) => {
          setShowModal(false)
          navigate(`/rooms/${id}`)
        }}
      />
    </Container>
  )
}
