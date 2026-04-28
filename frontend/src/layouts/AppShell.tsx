import { Button, Container, Nav, Navbar } from 'react-bootstrap'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function AppShell() {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      <Navbar
        bg="dark"
        data-bs-theme="dark"
        className="border-bottom"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <Container>
          <Navbar.Brand as={Link} to="/" className="fw-semibold">
            Travel Chat
          </Navbar.Brand>
          <Nav className="ms-auto align-items-center gap-3">
            {currentUser && (
              <span className="text-secondary">{currentUser.username}</span>
            )}
            <Button size="sm" variant="outline-secondary" onClick={handleLogout}>
              Logout
            </Button>
          </Nav>
        </Container>
      </Navbar>
      <Outlet />
    </>
  )
}
