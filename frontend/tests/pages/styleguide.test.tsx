import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

import Styleguide from '../../src/pages/_Styleguide'

describe('Styleguide page', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('renders a primary Button', () => {
    render(<Styleguide />)
    expect(screen.getAllByRole('button').length).toBeGreaterThan(0)
  })

  it('renders a Card section', () => {
    const { container } = render(<Styleguide />)
    expect(container.querySelector('.card')).not.toBeNull()
  })

  it('renders Form Controls (input and select)', () => {
    const { container } = render(<Styleguide />)
    expect(container.querySelector('input')).not.toBeNull()
    expect(container.querySelector('select')).not.toBeNull()
  })

  it('renders an Alert element', () => {
    const { container } = render(<Styleguide />)
    expect(container.querySelector('.alert')).not.toBeNull()
  })

  it('renders a Badge element', () => {
    const { container } = render(<Styleguide />)
    expect(container.querySelector('.badge')).not.toBeNull()
  })

  it('renders without console errors', () => {
    render(<Styleguide />)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
