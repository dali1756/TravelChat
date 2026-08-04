import { useCallback, useEffect, useState } from 'react'
import Alert from 'react-bootstrap/Alert'
import Badge from 'react-bootstrap/Badge'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import InputGroup from 'react-bootstrap/InputGroup'
import ListGroup from 'react-bootstrap/ListGroup'
import Modal from 'react-bootstrap/Modal'
import Spinner from 'react-bootstrap/Spinner'
import Stack from 'react-bootstrap/Stack'
import { searchUsers } from '../lib/chatApi'
import { toFieldErrors } from '../lib/formErrors'
import { addTripMember, fetchTripMembers, removeTripMember } from '../lib/tripApi'
import { tripRoleLabel } from '../lib/tripRoles'
import type { Peer, TripMember, TripMemberRole } from '../lib/types'

interface TripMembersModalProps {
  show: boolean
  tripId: number
  isOwner: boolean
  currentUserId: number | null
  onHide: () => void
  onLeft: () => void
}

export default function TripMembersModal({
  show,
  tripId,
  isOwner,
  currentUserId,
  onHide,
  onLeft,
}: TripMembersModalProps) {
  const [members, setMembers] = useState<TripMember[]>([])
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<Peer[]>([])
  const [roles, setRoles] = useState<Record<number, TripMemberRole>>({})
  const [messages, setMessages] = useState<string[]>([])
  const [busy, setBusy] = useState(false)

  const reloadMembers = useCallback(() => fetchTripMembers(tripId).then(setMembers), [tripId])

  useEffect(() => {
    if (!show) return
    setKeyword('')
    setResults([])
    setMessages([])
    reloadMembers().catch(() => setMessages(['載入成員失敗，請稍後再試。']))
  }, [show, reloadMembers])

  function report(err: unknown, fallback: string) {
    setMessages(Object.values(toFieldErrors(err, fallback, { preferServerDetail: true })).flat())
  }

  async function run(action: () => Promise<void>, fallback: string) {
    setBusy(true)
    setMessages([])
    try {
      await action()
    } catch (err) {
      report(err, fallback)
    } finally {
      setBusy(false)
    }
  }

  const handleSearch = () =>
    run(async () => {
      setResults(await searchUsers(keyword.trim()))
    }, '搜尋使用者失敗，請稍後再試。')

  const handleShare = (peer: Peer) =>
    run(async () => {
      await addTripMember(tripId, { user_id: peer.id, role: roles[peer.id] ?? 'viewer' })
      await reloadMembers()
      setResults((prev) => prev.filter((p) => p.id !== peer.id))
    }, '分享行程失敗，請稍後再試。')

  const handleRemove = (userId: number) =>
    run(async () => {
      await removeTripMember(tripId, userId)
      await reloadMembers()
    }, '移除成員失敗，請稍後再試。')

  const handleLeave = () =>
    run(async () => {
      if (currentUserId === null) return
      await removeTripMember(tripId, currentUserId)
      onLeft()
    }, '退出行程失敗，請稍後再試。')

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title as="h5">成員管理</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {messages.length > 0 && (
          <Alert variant="danger">
            {messages.map((msg) => (
              <div key={msg}>{msg}</div>
            ))}
          </Alert>
        )}

        {isOwner && (
          <>
            <Form.Group className="mb-2" controlId="member-search">
              <Form.Label>搜尋使用者</Form.Label>
              <InputGroup>
                <Form.Control type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="輸入使用者名稱" />
                <Button variant="outline-secondary" onClick={handleSearch} disabled={busy}>搜尋</Button>
              </InputGroup>
            </Form.Group>

            {results.length > 0 && (
              <ListGroup className="mb-3">
                {results.map((peer) => (
                  <ListGroup.Item key={peer.id} data-testid="user-result" className="d-flex justify-content-between align-items-center gap-2">
                    <span>{peer.username}</span>
                    <Stack direction="horizontal" gap={2}>
                      <Form.Select
                        size="sm"
                        aria-label={`指派 ${peer.username} 的角色`}
                        value={roles[peer.id] ?? 'viewer'}
                        onChange={(e) =>
                          setRoles((prev) => ({
                            ...prev,
                            [peer.id]: e.target.value as TripMemberRole,
                          }))
                        }
                      >
                        <option value="viewer">檢視者</option>
                        <option value="editor">編輯者</option>
                      </Form.Select>
                      <Button size="sm" onClick={() => handleShare(peer)} disabled={busy}>分享</Button>
                    </Stack>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            )}
          </>
        )}

        <h6>成員列表</h6>
        {members.length === 0 && <p className="text-muted mb-0">尚無其他成員。</p>}
        {members.length > 0 && (
          <ListGroup>
            {members.map((member) => (
              <ListGroup.Item key={member.id} data-testid="member-row" className="d-flex justify-content-between align-items-center">
                <span>{member.user.username}</span>
                <Stack direction="horizontal" gap={2}>
                  <Badge bg="secondary">{tripRoleLabel(member.role)}</Badge>
                  {isOwner && (
                    <Button size="sm" variant="outline-danger" onClick={() => handleRemove(member.user.id)} disabled={busy}>移除</Button>
                  )}
                </Stack>
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}
      </Modal.Body>
      <Modal.Footer>
        {!isOwner && (
          <Button variant="outline-danger" onClick={handleLeave} disabled={busy}>
            {busy ? <Spinner size="sm" /> : '退出行程'}
          </Button>
        )}
        <Button variant="outline-secondary" onClick={onHide}>關閉</Button>
      </Modal.Footer>
    </Modal>
  )
}
