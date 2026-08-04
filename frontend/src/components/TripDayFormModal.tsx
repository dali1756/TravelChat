import { useEffect, useState } from 'react'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Modal from 'react-bootstrap/Modal'
import Spinner from 'react-bootstrap/Spinner'
import { toFieldErrors, type FieldErrors } from '../lib/formErrors'
import type { TripDayInput } from '../lib/types'

const EMPTY: TripDayInput = { date: '', note: '' }

interface TripDayFormModalProps {
  show: boolean
  heading: string
  submitLabel: string
  initial?: TripDayInput
  onHide: () => void
  onSubmit: (payload: Required<TripDayInput>) => Promise<void>
}

export default function TripDayFormModal({
  show,
  heading,
  submitLabel,
  initial,
  onHide,
  onSubmit,
}: TripDayFormModalProps) {
  const [values, setValues] = useState<TripDayInput>(initial ?? EMPTY)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (show) {
      setValues(initial ?? EMPTY)
      setErrors({})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      await onSubmit({ date: values.date, note: values.note ?? '' })
    } catch (err) {
      setErrors(toFieldErrors(err, '儲存排程日期失敗，請稍後再試。'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title as="h5">{heading}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit} noValidate>
        <Modal.Body>
          {errors._root && <Alert variant="danger">{errors._root[0]}</Alert>}
          <Form.Group className="mb-3" controlId="day-date">
            <Form.Label>日期</Form.Label>
            <Form.Control
              type="date"
              value={values.date}
              onChange={(e) => setValues((prev) => ({ ...prev, date: e.target.value }))}
              isInvalid={!!errors.date}
              required
            />
            {errors.date?.map((msg) => (
              <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
            ))}
          </Form.Group>
          <Form.Group controlId="day-note">
            <Form.Label>備註</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={values.note ?? ''}
              onChange={(e) => setValues((prev) => ({ ...prev, note: e.target.value }))}
              isInvalid={!!errors.note}
            />
            {errors.note?.map((msg) => (
              <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
            ))}
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide} disabled={submitting}>取消</Button>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? <Spinner size="sm" /> : submitLabel}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  )
}
