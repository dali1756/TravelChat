import { useEffect, useMemo, useState } from 'react'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import InputGroup from 'react-bootstrap/InputGroup'
import Spinner from 'react-bootstrap/Spinner'
import { accessErrorMessage } from '../lib/formErrors'
import { createAttraction, fetchAttractions } from '../lib/tripApi'
import type { Attraction } from '../lib/types'

interface AttractionSelectProps {
  value: number | null
  onChange: (attractionId: number | null) => void
}

export default function AttractionSelect({ value, onChange }: AttractionSelectProps) {
  const [attractions, setAttractions] = useState<Attraction[]>([])
  const [keyword, setKeyword] = useState('')
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fetchAttractions()
      .then((data) => {
        if (active) setAttractions(data)
      })
      .catch(() => {
        if (active) setError('載入景點失敗，可改為建立新景點或不關聯景點。')
      })
    return () => {
      active = false
    }
  }, [])

  const visible = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    const matched = q
      ? attractions.filter(
          (a) => a.name.toLowerCase().includes(q) || a.address.toLowerCase().includes(q),
        )
      : attractions
    // 已選取的景點即使不符合搜尋條件也必須保留，否則 select 值會失效
    const selected = attractions.find((a) => a.id === value)
    return selected && !matched.some((a) => a.id === selected.id) ? [selected, ...matched] : matched
  }, [attractions, keyword, value])

  async function handleCreate() {
    const name = newName.trim()
    if (!name) return
    setCreating(true)
    setError(null)
    try {
      const created = await createAttraction({ name })
      setAttractions((prev) => [...prev, created])
      setNewName('')
      setKeyword('')
      onChange(created.id)
    } catch (err) {
      setError(accessErrorMessage(err, '建立景點失敗，請稍後再試。'))
    } finally {
      setCreating(false)
    }
  }

  return (
    <>
      <Form.Group className="mb-2" controlId="attraction-keyword">
        <Form.Label>搜尋景點</Form.Label>
        <Form.Control type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="輸入名稱或地址篩選" />
      </Form.Group>

      <Form.Group className="mb-2" controlId="attraction-select">
        <Form.Label>景點</Form.Label>
        <Form.Select value={value === null ? '' : String(value)} onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}>
          <option value="">不關聯景點</option>
          {visible.map((attraction) => (
            <option key={attraction.id} value={attraction.id}>
              {attraction.name}
            </option>
          ))}
        </Form.Select>
      </Form.Group>

      <Form.Group className="mb-2" controlId="attraction-new-name">
        <Form.Label>新增景點名稱</Form.Label>
        <InputGroup>
          <Form.Control type="text" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="找不到景點時可即時建立" />
          <Button variant="outline-secondary" onClick={handleCreate} disabled={creating}>
            {creating ? <Spinner size="sm" /> : '建立景點'}
          </Button>
        </InputGroup>
      </Form.Group>

      {error && <div className="text-danger small mb-2">{error}</div>}
    </>
  )
}
