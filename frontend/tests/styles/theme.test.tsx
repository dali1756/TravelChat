import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const STYLES_DIR = resolve(__dirname, '../../src/styles')

function read(file: string): string {
  return readFileSync(resolve(STYLES_DIR, file), 'utf-8')
}

describe('SCSS theme override', () => {
  it('_theme.scss overrides core Bootstrap variables before importing bootstrap', () => {
    const theme = read('_theme.scss')

    // core overrides
    for (const variable of [
      '$body-bg',
      '$body-color',
      '$primary',
      '$font-family-sans-serif',
      '$font-family-monospace',
    ]) {
      expect(theme).toMatch(new RegExp(`\\${variable}\\s*:`))
    }

    // primary must NOT be Bootstrap default blue #0d6efd
    expect(theme.toLowerCase()).not.toMatch(/\$primary\s*:\s*#0d6efd/)

    // bootstrap must be imported AFTER overrides
    const overrideIdx = theme.search(/\$body-bg\s*:/)
    const importIdx = theme.search(/@(?:import|use)\s+["'][^"']*bootstrap/)
    expect(overrideIdx).toBeGreaterThanOrEqual(0)
    expect(importIdx).toBeGreaterThan(overrideIdx)
  })

  it('global.css applies dark body background and Inter font-family', () => {
    const css = read('global.css')
    expect(css).toMatch(/body\s*\{[^}]*background[^}]*var\(--bg-app\)/s)
    expect(css).toMatch(/body\s*\{[^}]*font-family[^}]*var\(--font-family-sans\)/s)
  })

  it('index.scss imports tokens, theme, and global in order', () => {
    const idx = read('index.scss')
    const tokensIdx = idx.search(/tokens\.css/)
    const themeIdx = idx.search(/_theme/)
    const globalIdx = idx.search(/global\.css/)

    expect(tokensIdx).toBeGreaterThanOrEqual(0)
    expect(themeIdx).toBeGreaterThan(tokensIdx)
    expect(globalIdx).toBeGreaterThan(themeIdx)
  })
})
