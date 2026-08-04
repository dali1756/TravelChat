import { useEffect, useState } from 'react'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Modal from 'react-bootstrap/Modal'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Spinner from 'react-bootstrap/Spinner'
import AttractionSelect from './AttractionSelect'
import { EMPTY_ACTIVITY_FORM as EMPTY, type ActivityFormValues } from '../lib/activityForm'
import { toFieldErrors, type FieldErrors } from '../lib/formErrors'
import type { ActivityInput } from '../lib/types'

interface ActivityFormModalProps {
  show: boolean
  heading: string
  submitLabel: string
  initial?: ActivityFormValues
  onHide: () => void
  onSubmit: (payload: ActivityInput) => Promise<void>
}

export default function ActivityFormModal({
  show,
  heading,
  submitLabel,
  initial,
  onHide,
  onSubmit,
}: ActivityFormModalProps) {
  const [values, setValues] = useState<ActivityFormValues>(initial ?? EMPTY)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (show) {
      setValues(initial ?? EMPTY)
      setErrors({})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  function update<K extends keyof ActivityFormValues>(field: K, value: ActivityFormValues[K]) {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      await onSubmit({
        title: values.title,
        attraction_id: values.attraction_id,
        start_time: values.start_time || null,
        end_time: values.end_time || null,
        note: values.note,
      })
    } catch (err) {
      setErrors(toFieldErrors(err, '儲存活動失敗，請稍後再試。'))
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
          <Form.Group className="mb-3" controlId="activity-title">
            <Form.Label>標題</Form.Label>
            <Form.Control type="text" value={values.title} onChange={(e) => update('title', e.target.value)} isInvalid={!!errors.title} required />
            {errors.title?.map((msg) => (
              <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
            ))}
          </Form.Group>
          <AttractionSelect value={values.attraction_id} onChange={(attractionId) => update('attraction_id', attractionId)} />

          <Row className="mb-3 mt-3">
            <Col>
              <Form.Group controlId="activity-start-time">
                <Form.Label>開始時間</Form.Label>
                <Form.Control type="time" value={values.start_time} onChange={(e) => update('start_time', e.target.value)} isInvalid={!!errors.start_time} />
                {errors.start_time?.map((msg) => (
                  <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
                ))}
              </Form.Group>
            </Col>
            <Col>
              <Form.Group controlId="activity-end-time">
                <Form.Label>結束時間</Form.Label>
                <Form.Control type="time" value={values.end_time} onChange={(e) => update('end_time', e.target.value)} isInvalid={!!errors.end_time} />
                {errors.end_time?.map((msg) => (
                  <Form.Control.Feedback key={msg} type="invalid">{msg}</Form.Control.Feedback>
                ))}
              </Form.Group>
            </Col>
          </Row>
          <Form.Group controlId="activity-note">
            <Form.Label>備註</Form.Label>
            <Form.Control as="textarea" rows={2} value={values.note} onChange={(e) => update('note', e.target.value)} isInvalid={!!errors.note} />
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
