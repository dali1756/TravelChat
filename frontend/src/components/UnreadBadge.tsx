import Badge from 'react-bootstrap/Badge'

interface Props {
  count: number
}

export default function UnreadBadge({ count }: Props) {
  if (count <= 0) return null
  return (
    <Badge bg="primary" pill data-testid="unread-badge">
      {count}
    </Badge>
  )
}
