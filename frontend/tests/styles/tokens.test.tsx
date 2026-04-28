import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const tokensRaw = readFileSync(
  resolve(__dirname, '../../src/styles/tokens.css'),
  'utf-8',
)

const REQUIRED_TOKENS = [
  '--bg-app',
  '--bg-surface',
  '--bg-surface-alt',
  '--bg-elevated',
  '--border-subtle',
  '--text-primary',
  '--text-secondary',
  '--accent',
  '--font-size-body',
  '--font-family-sans',
  '--font-family-mono',
]

function getTokenValue(css: string, name: string): string | null {
  const match = css.match(
    new RegExp(`${name.replace(/-/g, '\\-')}\\s*:\\s*([^;]+);`),
  )
  return match ? match[1].trim() : null
}

describe('design tokens', () => {
  it('declares :root block', () => {
    expect(tokensRaw).toMatch(/:root\s*\{/)
  })

  it.each(REQUIRED_TOKENS)('defines %s with a non-empty value', (token) => {
    const value = getTokenValue(tokensRaw, token)
    expect(value).not.toBeNull()
    expect(value).not.toBe('')
  })

  it('--bg-app is not pure black', () => {
    const value = getTokenValue(tokensRaw, '--bg-app')!.toLowerCase()
    expect(value).not.toBe('#000')
    expect(value).not.toBe('#000000')
    expect(value).not.toBe('rgb(0, 0, 0)')
    expect(value).not.toBe('black')
  })
})
