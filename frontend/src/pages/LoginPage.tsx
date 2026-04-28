import { useState } from 'react'
import { Alert, Button, Card, Container, Form, Spinner, Stack } from 'react-bootstrap'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../lib/api'

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (isAuthenticated) {
    const from =
      (location.state as { from?: string } | null)?.from ?? '/'
    return <Navigate to={from} replace />
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login(email, password)
      const from = (location.state as { from?: string } | null)?.from ?? '/'
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('登入失敗，請稍後再試。')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Container className="py-5" style={{ maxWidth: 420 }}>
      <Card>
        <Card.Body>
          <Stack gap={3}>
            <div>
              <h1 className="h4 mb-1">Login</h1>
              <p className="text-muted mb-0">登入您的 Travel Chat 帳號。</p>
            </div>
            {error && <Alert variant="danger">{error}</Alert>}
            <Form onSubmit={handleSubmit} noValidate>
              <Form.Group className="mb-3" controlId="login-email">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </Form.Group>
              <Form.Group className="mb-4" controlId="login-password">
                <Form.Label>Password</Form.Label>
                <Form.Control
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </Form.Group>
              <Button type="submit" variant="primary" disabled={submitting} className="w-100">
                {submitting ? <Spinner size="sm" /> : 'Login'}
              </Button>
            </Form>
            <div className="text-center text-muted small">
              還沒有帳號？<Link to="/register">註冊</Link>
            </div>
          </Stack>
        </Card.Body>
      </Card>
    </Container>
  )
}
