import { useEffect, useState } from 'react'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Modal from 'react-bootstrap/Modal'
import Spinner from 'react-bootstrap/Spinner'
import { toFieldErrors, type FieldErrors } from '../lib/formErrors'
import type { TripInput } from '../lib/types'

const EMPTY: TripInput = { title: '', description: '', start_date: '', end_date: '' }

interface TripFormModalProps {
  show: boolean
  heading: string
  submitLabel: string
  initial?: TripInput
  onHide: () => void
  onSubmit: (payload: TripInput) => Promise<void>
}

export default function TripFormModal({
  show,
  heading,
  submitLabel,
  initial,
  onHide,
  onSubmit,
}: TripFormModalProps) {
  const [values, setValues] = useState<TripInput>(initial ?? EMPTY)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (show) {
      setValues(initial ?? EMPTY)
      setErrors({})
    }
    // 僅在開啟瞬間重設，避免輸入過程被父層 re-render 覆寫
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  function update(field: keyof TripInput, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      await onSubmit({ ...values, description: values.description ?? '' })
    } catch (err) {
      setErrors(toFieldErrors(err, '儲存行程失敗，請稍後再試。'))
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
          <Form.Group className="mb-3" controlId="trip-title">
            <Form.Label>標題</Form.Label>
            <Form.Control type="text" value={values.title} onChange={(e) => update('title', e.target.value)} isInvalid={!!errors.title} required />
            {errors.title?.map((msg) => (
              <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
            ))}
          </Form.Group>
          <Form.Group className="mb-3" controlId="trip-description">
            <Form.Label>描述</Form.Label>
            <Form.Control as="textarea" rows={2} value={values.description ?? ''} onChange={(e) => update('description', e.target.value)} isInvalid={!!errors.description} />
            {errors.description?.map((msg) => (
              <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
            ))}
          </Form.Group>
          <Form.Group className="mb-3" controlId="trip-start-date">
            <Form.Label>起始日期</Form.Label>
            <Form.Control type="date" value={values.start_date} onChange={(e) => update('start_date', e.target.value)} isInvalid={!!errors.start_date} required />
            {errors.start_date?.map((msg) => (
              <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
            ))}
          </Form.Group>
          <Form.Group controlId="trip-end-date">
            <Form.Label>結束日期</Form.Label>
            <Form.Control type="date" value={values.end_date} onChange={(e) => update('end_date', e.target.value)} isInvalid={!!errors.end_date} required />
            {errors.end_date?.map((msg) => (
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
