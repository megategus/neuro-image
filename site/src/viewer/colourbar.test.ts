import { afterEach, describe, expect, it, vi } from 'vitest'
import { cmapper } from '@niivue/niivue'
import { colormapGradient } from './colourbar'

afterEach(() => vi.restoreAllMocks())

describe('colormapGradient', () => {
  it("builds the gradient from NiiVue's colour-map control points", () => {
    const spy = vi.spyOn(cmapper, 'colormapFromKey').mockReturnValue({
      R: [10, 20], G: [30, 40], B: [50, 60], A: [0, 255], I: [0, 255],
    })
    expect(colormapGradient('anything')).toBe(
      'linear-gradient(90deg, rgb(10, 30, 50) 0%, rgb(20, 40, 60) 100%)',
    )
    expect(spy).toHaveBeenCalledWith('anything')
  })

  it("matches NiiVue 0.69's real warm and winter maps", () => {
    expect(colormapGradient('warm')).toBe(
      'linear-gradient(90deg, rgb(255, 127, 0) 0%, rgb(255, 196, 0) 50.2%, rgb(255, 254, 0) 100%)',
    )
    expect(colormapGradient('winter')).toBe(
      'linear-gradient(90deg, rgb(0, 0, 255) 0%, rgb(0, 128, 196) 50.2%, rgb(0, 255, 128) 100%)',
    )
  })
})
