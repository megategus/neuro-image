import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@niivue/niivue', () => {
  class Niivue {
    sliceTypeMultiplanar = 3
    opts: Record<string, unknown> = {}
    onLocationChange = () => {}
    attachToCanvas = vi.fn().mockResolvedValue(this)
    loadVolumes = vi.fn().mockResolvedValue(this)
    setSliceType = vi.fn()
    drawScene = vi.fn()
    volumes = []
    cleanup = vi.fn()
  }
  return { Niivue, SHOW_RENDER: { NEVER: 0, ALWAYS: 1, AUTO: 2 } }
})

import BrainViewer from './BrainViewer'
import { fixtureMap } from '../testFixtures'

afterEach(() => vi.restoreAllMocks())

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
})
