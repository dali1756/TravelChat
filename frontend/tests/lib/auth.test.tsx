import { describe, it, expect, beforeEach } from 'vitest'
import { auth } from '../../src/lib/auth'

describe('auth token storage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns null when nothing is stored', () => {
    expect(auth.getAccess()).toBeNull()
    expect(auth.getRefresh()).toBeNull()
  })

  it('persists access and refresh tokens via set()', () => {
    auth.set('a-token', 'r-token')
    expect(auth.getAccess()).toBe('a-token')
    expect(auth.getRefresh()).toBe('r-token')
  })

  it('overwrites previous values when set() is called again', () => {
    auth.set('a1', 'r1')
    auth.set('a2', 'r2')
    expect(auth.getAccess()).toBe('a2')
    expect(auth.getRefresh()).toBe('r2')
  })

  it('clears both tokens', () => {
    auth.set('a', 'r')
    auth.clear()
    expect(auth.getAccess()).toBeNull()
    expect(auth.getRefresh()).toBeNull()
  })
})
