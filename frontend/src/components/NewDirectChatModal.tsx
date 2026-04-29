import { useState } from 'react'
import Modal from 'react-bootstrap/Modal'
import Form from 'react-bootstrap/Form'
import ListGroup from 'react-bootstrap/ListGroup'
import Spinner from 'react-bootstrap/Spinner'
import { createDirectRoom, searchUsers } from '../lib/chatApi'
import type { Peer } from '../lib/types'

interface Props {
  show: boolean
  onHide(): void
  onRoomSelected(roomId: number): void
}

export default function NewDirectChatModal({ show, onHide, onRoomSelected }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Peer[]>([])
  const [searching, setSearching] = useState(false)
  const [creating, setCreating] = useState(false)

  function handleQueryChange(value: string) {
    setQuery(value)
    if (value.trim().length < 1) {
      setResults([])
      return
    }
    setSearching(true)
    searchUsers(value.trim())
      .then(setResults)
      .catch(() => setResults([]))
      .finally(() => setSearching(false))
  }

  async function handleSelect(peer: Peer) {
    setCreating(true)
    try {
      const room = await createDirectRoom(peer.id)
      onRoomSelected(room.id)
    } finally {
      setCreating(false)
    }
  }

  function handleHide() {
    setQuery('')
    setResults([])
    onHide()
  }

  return (
    <Modal show={show} onHide={handleHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>新增對話</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form.Control
          placeholder="搜尋使用者名稱…"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          autoFocus
        />

        <div className="mt-2">
          {searching && <Spinner animation="border" size="sm" />}

          {!searching && query.trim().length >= 1 && results.length === 0 && (
            <p className="text-muted mt-2">找不到符合的使用者。</p>
          )}

          {results.length > 0 && (
            <ListGroup className="mt-2">
              {results.map((peer) => (
                <ListGroup.Item
                  key={peer.id}
                  action
                  disabled={creating}
                  onClick={() => handleSelect(peer)}
                >
                  {peer.username}
                </ListGroup.Item>
              ))}
            </ListGroup>
          )}
        </div>
      </Modal.Body>
    </Modal>
  )
}
