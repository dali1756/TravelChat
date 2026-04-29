import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Alert from 'react-bootstrap/Alert'
import Spinner from 'react-bootstrap/Spinner'
import { ApiError, apiFetch } from '../lib/api'
import { fetchMessages, markRoomRead } from '../lib/chatApi'
import type { Message } from '../lib/types'
import { auth } from '../lib/auth'
import MessageBubble from '../components/MessageBubble'
import { useAuth } from '../auth/AuthContext'

export default function ChatRoomPage() {
  const { id } = useParams<{ id: string }>()
  const roomId = Number(id)
  const navigate = useNavigate()
  const { currentUser } = useAuth()

  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [accessError, setAccessError] = useState(false)
  const [wsDisconnected, setWsDisconnected] = useState(false)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    fetchMessages(roomId)
      .then((msgs) => {
        setMessages(msgs)
        markRoomRead(roomId).catch(() => {})
      })
      .catch((err) => {
        if (err instanceof ApiError && (err.status === 403 || err.status === 404)) {
          setAccessError(true)
        }
      })
      .finally(() => setLoading(false))
  }, [roomId])

  useEffect(() => {
    if (loading || accessError) return

    const token = auth.getAccess()
    const wsBase = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000'
    const ws = new WebSocket(`${wsBase}/ws/chat/${roomId}/?token=${token}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'message.new') {
        const msg: Message = data.message
        setMessages((prev) =>
          prev.some((m) => m.id === msg.id) ? prev : [...prev, msg],
        )
        if (msg.sender_id !== currentUser?.id) {
          markRoomRead(roomId).catch(() => {})
        }
      }
    }

    ws.onerror = () => setWsDisconnected(true)
    ws.onclose = () => setWsDisconnected(true)

    return () => {
      ws.close()
    }
  }, [loading, accessError, roomId, currentUser])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function sendMessage() {
    const text = input.trim()
    if (!text || !wsRef.current) return
    wsRef.current.send(JSON.stringify({ type: 'message.send', content: text }))
    setInput('')
  }

  if (loading) return <Spinner animation="border" className="m-4" />

  if (accessError) {
    return (
      <Container className="py-4">
        <Alert variant="danger">無法存取此聊天室。</Alert>
        <Button variant="link" onClick={() => navigate('/rooms')}>
          返回列表
        </Button>
      </Container>
    )
  }

  return (
    <Container className="py-3 d-flex flex-column" style={{ height: 'calc(100vh - 60px)' }}>
      <div className="mb-2">
        <Button variant="link" className="p-0" onClick={() => navigate('/rooms')}>
          ← 返回列表
        </Button>
      </div>

      {wsDisconnected && (
        <Alert variant="warning" className="py-1">
          連線已中斷，請重新整理。
        </Alert>
      )}

      <div className="flex-grow-1 overflow-auto mb-3">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} isMine={msg.sender_id === currentUser?.id} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <Form
        onSubmit={(e) => {
          e.preventDefault()
          sendMessage()
        }}
        className="d-flex gap-2"
      >
        <Form.Control
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="輸入訊息…"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              sendMessage()
            }
          }}
        />
        <Button type="submit">送出</Button>
      </Form>
    </Container>
  )
}
