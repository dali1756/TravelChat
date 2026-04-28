import { useState } from 'react'
import { Alert, Button, Card, Container, Form, Spinner, Stack } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../lib/api'

type FieldErrors = Partial<Record<'email' | 'username' | 'password' | '_root', string[]>>

export default function RegisterPage() {
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [done, setDone] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      await register({ email, username, password })
      setDone(true)
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === 'object') {
        const next: FieldErrors = {}
        for (const [key, val] of Object.entries(err.body as Record<string, unknown>)) {
          if (Array.isArray(val) && val.every((v) => typeof v === 'string')) {
            next[key as keyof FieldErrors] = val as string[]
          }
        }
        setErrors(next)
      } else {
        setErrors({ _root: ['註冊失敗，請稍後再試。'] })
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
              <h1 className="h4 mb-1">Register</h1>
              <p className="text-muted mb-0">建立 Travel Chat 帳號。</p>
            </div>
            {done && (
              <Alert variant="success">
                註冊成功，請至信箱完成驗證後再登入。
              </Alert>
            )}
            {errors._root && <Alert variant="danger">{errors._root[0]}</Alert>}
            {!done && (
              <Form onSubmit={handleSubmit} noValidate>
                <Form.Group className="mb-3" controlId="reg-email">
                  <Form.Label>Email</Form.Label>
                  <Form.Control
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    isInvalid={!!errors.email}
                    autoComplete="email"
                    required
                  />
                  {errors.email?.map((msg) => (
                    <Form.Control.Feedback key={msg} type="invalid">
                      {msg}
                    </Form.Control.Feedback>
                  ))}
                </Form.Group>
                <Form.Group className="mb-3" controlId="reg-username">
                  <Form.Label>Username</Form.Label>
                  <Form.Control
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    isInvalid={!!errors.username}
                    autoComplete="username"
                    required
                  />
                  {errors.username?.map((msg) => (
                    <Form.Control.Feedback key={msg} type="invalid">
                      {msg}
                    </Form.Control.Feedback>
                  ))}
                </Form.Group>
                <Form.Group className="mb-4" controlId="reg-password">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    isInvalid={!!errors.password}
                    autoComplete="new-password"
                    required
                  />
                  {errors.password?.map((msg) => (
                    <Form.Control.Feedback key={msg} type="invalid">
                      {msg}
                    </Form.Control.Feedback>
                  ))}
                </Form.Group>
                <Button type="submit" variant="primary" disabled={submitting} className="w-100">
                  {submitting ? <Spinner size="sm" /> : 'Register'}
                </Button>
              </Form>
            )}
            <div className="text-center text-muted small">
              已經有帳號？<Link to="/login">登入</Link>
            </div>
          </Stack>
        </Card.Body>
      </Card>
    </Container>
  )
}
