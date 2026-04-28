import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const SRC_DIR = resolve(__dirname, '../../src')

describe('font loading', () => {
  const mainSource = readFileSync(resolve(SRC_DIR, 'main.tsx'), 'utf-8')

  it.each([
    '@fontsource/inter/400.css',
    '@fontsource/inter/500.css',
    '@fontsource/inter/600.css',
    '@fontsource/inter/700.css',
    '@fontsource/jetbrains-mono/400.css',
    '@fontsource/jetbrains-mono/500.css',
  ])('main.tsx imports %s', (path) => {
    expect(mainSource).toContain(path)
  })

  it('main.tsx imports the styles entry after fonts', () => {
    const interIdx = mainSource.search(/@fontsource\/inter/)
    const stylesIdx = mainSource.search(/styles\/index\.scss/)
    expect(interIdx).toBeGreaterThanOrEqual(0)
    expect(stylesIdx).toBeGreaterThan(interIdx)
  })

  it('main.tsx no longer imports the original bootstrap.min.css', () => {
    expect(mainSource).not.toMatch(/bootstrap\/dist\/css\/bootstrap\.min\.css/)
  })

  const tokensRaw = readFileSync(resolve(SRC_DIR, 'styles/tokens.css'), 'utf-8')

  it('tokens.css declares Inter as the sans family', () => {
    const sans = tokensRaw.match(/--font-family-sans\s*:\s*([^;]+);/)?.[1]
    expect(sans).toBeDefined()
    expect(sans!.toLowerCase()).toContain('inter')
  })

  it('tokens.css declares JetBrains Mono as the mono family', () => {
    const mono = tokensRaw.match(/--font-family-mono\s*:\s*([^;]+);/)?.[1]
    expect(mono).toBeDefined()
    expect(mono!.toLowerCase()).toContain('jetbrains mono')
  })
})
