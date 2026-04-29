import type { Message } from '../lib/types'

interface Props {
  message: Message
  isMine: boolean
}

export default function MessageBubble({ message, isMine }: Props) {
  return (
    <div className={`d-flex mb-2 ${isMine ? 'justify-content-end' : 'justify-content-start'}`}>
      <div
        className={`px-3 py-2 rounded-3 ${isMine ? 'bg-primary text-white' : 'bg-secondary-subtle'}`}
        style={{ maxWidth: '70%' }}
        data-testid="message-bubble"
      >
        {!isMine && (
          <div className="fw-semibold small mb-1">{message.sender_username}</div>
        )}
        <div>{message.content}</div>
      </div>
    </div>
  )
}
