import { useEffect, useState } from 'react'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import Modal from 'react-bootstrap/Modal'
import Spinner from 'react-bootstrap/Spinner'
import { accessErrorMessage } from '../lib/formErrors'

interface ConfirmModalProps {
  show: boolean
  heading: string
  body: string
  confirmLabel: string
  onHide: () => void
  onConfirm: () => Promise<void>
}

export default function ConfirmModal({
  show,
  heading,
  body,
  confirmLabel,
  onHide,
  onConfirm,
}: ConfirmModalProps) {
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (show) setError(null)
  }, [show])

  async function handleConfirm() {
    setSubmitting(true)
    setError(null)
    try {
      await onConfirm()
    } catch (err) {
      setError(accessErrorMessage(err, err instanceof Error ? err.message : '操作失敗，請稍後再試。'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title as="h5">{heading}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        <p className="mb-0">{body}</p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="outline-secondary" onClick={onHide} disabled={submitting}>取消</Button>
        <Button variant="danger" onClick={handleConfirm} disabled={submitting}>
          {submitting ? <Spinner size="sm" /> : confirmLabel}
        </Button>
      </Modal.Footer>
    </Modal>
  )
}
