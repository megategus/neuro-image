import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

const h = vi.hoisted(() => ({
  instances: [] as {
    loadVolumes: ReturnType<typeof vi.fn>
    updateGLVolume: ReturnType<typeof vi.fn>
    broadcastTo: ReturnType<typeof vi.fn>
    mm2frac: ReturnType<typeof vi.fn>
    volumes: Record<string, number>[]
    scene: { crosshairPos: number[] }
  }[],
  loseContext: vi.fn(),
}))

vi.mock('@niivue/niivue', () => {
  class Niivue {
    sliceTypeMultiplanar = 3
    onLocationChange = () => {}
    volumes: Record<string, number>[] = []
    scene = { crosshairPos: [0, 0, 0] }
    gl = { getExtension: () => ({ loseContext: h.loseContext }) }
    attachToCanvas = vi.fn().mockResolvedValue(this)
    loadVolumes = vi.fn().mockImplementation(async (l: unknown[]) => {
      this.volumes = l.map(() => ({}))
      return this
    })
    setSliceType = vi.fn()
    mm2frac = vi.fn().mockImplementation((mm: number[]) => mm.map((v) => v / 100))
    frac2mm = vi.fn().mockImplementation((f: number[]) => f.map((v) => v * 100))
    broadcastTo = vi.fn()
    drawScene = vi.fn()
    updateGLVolume = vi.fn()
    cleanup = vi.fn()
    constructor() {
      h.instances.push(this)
    }
  }
  const cmapper = {
    colormapFromKey: (name: string) =>
      name === 'warm'
        ? { R: [1, 2], G: [3, 4], B: [5, 6], A: [0, 0], I: [0, 255] }
        : { R: [7, 8], G: [9, 10], B: [11, 12], A: [0, 0], I: [0, 255] },
  }
  return { Niivue, cmapper, SHOW_RENDER: { NEVER: 0, ALWAYS: 1, AUTO: 2 } }
})

import BrainViewer from './BrainViewer'
import { fixtureMap } from '../testFixtures'

afterEach(() => {
  vi.restoreAllMocks()
  h.instances.length = 0
  h.loseContext.mockClear()
})

describe('BrainViewer', () => {
  it('renders the WebGL2 fallback when no webgl2 context exists', () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
    render(<BrainViewer maps={[fixtureMap()]} cut={null} showLabels={false} />)
    expect(
      screen.getByText(
        '3D view needs WebGL2, which this browser does not provide. The map details and network profiles below still work.',
      ),
    ).toBeInTheDocument()
  })

  it('renders one viewer group per study', () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    render(
      <BrainViewer
        maps={[fixtureMap(), fixtureMap({ id: 'retrieval', label: 'Retrieval', study_id: 'other' })]}
        cut={null}
        showLabels={false}
      />,
    )
    expect(screen.getAllByTestId('viewer-group')).toHaveLength(2)
  })

  it('renders one canvas per map within a group', () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const { container } = render(
      <BrainViewer maps={[fixtureMap(), fixtureMap({ id: 'anger', label: 'Anger' })]} cut={null} showLabels={false} />,
    )
    expect(screen.getAllByTestId('viewer-group')).toHaveLength(1)
    expect(container.querySelectorAll('canvas')).toHaveLength(2)
  })

  it('releases the WebGL context on unmount', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const { unmount } = render(<BrainViewer maps={[fixtureMap()]} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances[0].loadVolumes).toHaveBeenCalled())
    unmount()
    expect(h.loseContext).toHaveBeenCalled()
  })

  it('does not reload volumes when the cut changes, only updates cal_min', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const { rerender } = render(<BrainViewer maps={[fixtureMap()]} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances.at(-1)!.volumes.length).toBe(2))
    const nv = h.instances.at(-1)!
    expect(nv.loadVolumes).toHaveBeenCalledTimes(1)
    const map = [fixtureMap()]
    rerender(<BrainViewer maps={map} cut={0.04} showLabels={false} />)
    await waitFor(() => expect(nv.volumes[1].cal_min).toBe(0.04))
    expect(nv.loadVolumes).toHaveBeenCalledTimes(1)
    expect(nv.updateGLVolume).toHaveBeenCalled()
  })

  it('applies the cut only to the wager group', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const other = fixtureMap({ id: 'retrieval', label: 'Retrieval', study_id: 'other', display_min: 0.5, display_max: 3 })
    render(<BrainViewer maps={[fixtureMap(), other]} cut={0.04} showLabels={false} />)
    await waitFor(() => expect(h.instances.length).toBe(2))
    await waitFor(() => expect(h.instances.every((i) => i.volumes.length === 2 && i.volumes[1].cal_min !== undefined)).toBe(true))
    const mins = h.instances.map((i) => i.volumes[1].cal_min).sort()
    expect(mins).toEqual([0.04, 0.5])
  })

  it('synchronises crosshair and 3D view within a group, never across groups', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const other = fixtureMap({ id: 'retrieval', label: 'Retrieval', study_id: 'other' })
    render(<BrainViewer maps={[fixtureMap(), fixtureMap({ id: 'anger', label: 'Anger' }), other]} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances.every((i) => i.volumes.length === 2)).toBe(true))
    const [fear, anger, retrieval] = h.instances
    expect(fear.broadcastTo).toHaveBeenLastCalledWith([anger], { '2d': true, '3d': true })
    expect(anger.broadcastTo).toHaveBeenLastCalledWith([fear], { '2d': true, '3d': true })
    expect(retrieval.broadcastTo).toHaveBeenLastCalledWith([], { '2d': true, '3d': true })
  })

  it('unlinks a canvas from its group when its map is removed', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const fear = fixtureMap()
    const anger = fixtureMap({ id: 'anger', label: 'Anger' })
    const { rerender } = render(<BrainViewer maps={[fear, anger]} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances.every((i) => i.volumes.length === 2)).toBe(true))
    const nvFear = h.instances[0]
    rerender(<BrainViewer maps={[fear]} cut={null} showLabels={false} />)
    await waitFor(() => expect(nvFear.broadcastTo).toHaveBeenLastCalledWith([], { '2d': true, '3d': true }))
  })

  it('starts the crosshair at the volume centre', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    render(<BrainViewer maps={[fixtureMap()]} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances[0].volumes.length).toBe(2))
    await waitFor(() => expect(h.instances[0].scene.crosshairPos).toEqual([0.5, 0.5, 0.5]))
    expect(h.instances[0].mm2frac).not.toHaveBeenCalledWith([22, -4, -12])
  })

  it("keeps fear's colour range when sadness is added (study-wide scale)", async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    const all = [
      fixtureMap({ display_max: 0.0877 }),
      fixtureMap({ id: 'sadness', label: 'Sadness', display_max: 0.09 }),
      fixtureMap({ id: 'anger', label: 'Anger', display_max: 0.1207 }),
    ]
    const { rerender } = render(<BrainViewer maps={[all[0]]} allMaps={all} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances[0].volumes[1]?.cal_max).toBe(0.1207))
    rerender(<BrainViewer maps={[all[0], all[1]]} allMaps={all} cut={null} showLabels={false} />)
    await waitFor(() => expect(h.instances.length).toBe(2))
    await waitFor(() => expect(h.instances[1].volumes[1]?.cal_max).toBe(0.1207))
    expect(h.instances[0].volumes[1].cal_max).toBe(0.1207)
  })

  it("draws the colour bar from NiiVue's colour-map stops", () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({} as never)
    render(<BrainViewer maps={[fixtureMap({ has_negative: true, files: { pos: 'p', neg: 'n' } })]} cut={null} showLabels={false} />)
    expect(screen.getByTestId('colourbar-warm').style.background).toContain('rgb(1, 3, 5)')
    expect(screen.getByTestId('colourbar-cool').style.background).toContain('rgb(8, 10, 12)')
  })
})
