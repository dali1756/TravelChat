import {
  Alert,
  Badge,
  Button,
  Card,
  Container,
  Form,
  Stack,
} from 'react-bootstrap'

export default function Styleguide() {
  return (
    <Container className="py-5">
      <Stack gap={5}>
        <header>
          <h1 className="mb-2">Travel Chat — Design System</h1>
          <p className="text-muted mb-0">
            設計系統參考頁。展示套用 design tokens 後的常用元件外觀。
          </p>
        </header>

        <section>
          <h2 className="h4 mb-3">Buttons</h2>
          <Stack direction="horizontal" gap={2} className="flex-wrap">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="success">Success</Button>
            <Button variant="danger">Danger</Button>
            <Button variant="warning">Warning</Button>
            <Button variant="info">Info</Button>
            <Button variant="outline-primary">Outline</Button>
            <Button variant="primary" disabled>
              Disabled
            </Button>
          </Stack>
        </section>

        <section>
          <h2 className="h4 mb-3">Cards</h2>
          <Card>
            <Card.Body>
              <Card.Title>Sample card</Card.Title>
              <Card.Text className="text-muted mb-3">
                卡片用於 chat room、AI 回應、行程片段等資訊區塊。
              </Card.Text>
              <Button variant="primary" size="sm">
                View detail
              </Button>
            </Card.Body>
          </Card>
        </section>

        <section>
          <h2 className="h4 mb-3">Form Controls</h2>
          <Form>
            <Form.Group className="mb-3" controlId="sg-input">
              <Form.Label>Email</Form.Label>
              <Form.Control type="email" placeholder="you@example.com" />
              <Form.Text className="text-muted">
                這是輸入框的提示文字。
              </Form.Text>
            </Form.Group>
            <Form.Group className="mb-3" controlId="sg-select">
              <Form.Label>Region</Form.Label>
              <Form.Select defaultValue="tw">
                <option value="tw">Taiwan</option>
                <option value="jp">Japan</option>
                <option value="us">United States</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3" controlId="sg-disabled-input">
              <Form.Label>Disabled</Form.Label>
              <Form.Control type="text" placeholder="Disabled" disabled />
            </Form.Group>
          </Form>
        </section>

        <section>
          <h2 className="h4 mb-3">Alerts</h2>
          <Stack gap={2}>
            <Alert variant="primary">Primary alert — accent 色提示。</Alert>
            <Alert variant="success">Success alert — 操作完成。</Alert>
            <Alert variant="warning">Warning alert — 需要使用者確認。</Alert>
            <Alert variant="danger">Danger alert — 操作失敗或錯誤。</Alert>
          </Stack>
        </section>

        <section>
          <h2 className="h4 mb-3">Badges</h2>
          <Stack direction="horizontal" gap={2} className="flex-wrap">
            <Badge bg="primary">Unread 3</Badge>
            <Badge bg="secondary">Beta</Badge>
            <Badge bg="success">Online</Badge>
            <Badge bg="warning" text="dark">
              Pending
            </Badge>
            <Badge bg="danger">Failed</Badge>
            <Badge bg="info">Info</Badge>
          </Stack>
        </section>
      </Stack>
    </Container>
  )
}
