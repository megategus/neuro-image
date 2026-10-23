import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureMap } from './testFixtures'

vi.mock('./viewer/BrainViewer', () => ({
  default: ({ maps, cut }: { maps: unknown[]; cut: number | null }) => (
    <div data-testid="viewer-group" data-cut={String(cut)}>{maps.length} maps</div>
  ),
}))
vi.mock('./data/load', () => ({
  loadAll: async () => ({
    maps: [fixtureMap({ id: 'fear', label: 'Fear' }), fixtureMap({ id: 'anger', label: 'Anger' })],
    unavailable: [{ id: 'anxiety', label: 'Anxiety', reason: 'source not yet verified' }],
    profiles: [], regions: [], atlasLabels: false,
    atlas: {
      labels: {},
      template: { name: 'MNI template', licence: 'MNI licence: Copyright (C) 1993-2004 Louis Collins' },
      sources: [{ name: 'Yeo', citation: 'Yeo 2011', licence: 'MIT (CBIG)', bundled: true }],
    },
    lessons: {
      lessons: [
        { id: 'a', title: 'One', map_ids: ['fear'], view: 'overlay', reviewed: true, body: ['x'], notice: 'n', claims: [] },
        { id: 'b', title: 'Two', map_ids: ['anger', 'fear'], view: 'both', reviewed: true, body: ['x'], notice: 'n', claims: [] },
        { id: 'c', title: 'Three', map_ids: ['fear', 'anxiety'], view: 'both', reviewed: true, body: ['x'], notice: 'n', claims: [] },
      ],
    },
  }),
}))

import App from './App'

describe('App guided lessons', () => {
  it('shows no viewer once an unavailable lesson is current, and restores it going back', async () => {
    render(<App />)
    await screen.findByRole('heading', { name: 'One' })
    await waitFor(() => expect(screen.getByTestId('viewer-group')).toHaveTextContent('1 maps'))
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    await waitFor(() => expect(screen.getByTestId('viewer-group')).toHaveTextContent('2 maps'))
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    await screen.findByText('This lesson needs data not yet available')
    await waitFor(() => expect(screen.queryByTestId('viewer-group')).toBeNull())
    fireEvent.click(screen.getByRole('button', { name: 'Previous' }))
    await waitFor(() => expect(screen.getByTestId('viewer-group')).toHaveTextContent('2 maps'))
  })
})

describe('App display cut', () => {
  const AUTHORS = 'display threshold chosen by the authors — not a significance test'

  it('labels the cut actually in use: authors default, user cut, unthresholded', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('viewer-group')).toHaveTextContent('1 maps'))
    const label = screen.getByTestId('cut-label')
    expect(label).toHaveTextContent(AUTHORS)
    expect(screen.getByTestId('viewer-group')).toHaveAttribute('data-cut', 'null')

    fireEvent.change(screen.getByRole('slider'), { target: { value: '0.02' } })
    expect(label).toHaveTextContent(
      "display cut set by you: 0.02 — not a significance test (authors' display threshold: 0.001)",
    )
    expect(label).not.toHaveTextContent('chosen by the authors')
    expect(screen.getByTestId('viewer-group')).toHaveAttribute('data-cut', '0.02')

    fireEvent.change(screen.getByRole('slider'), { target: { value: '0.001' } })
    expect(label).toHaveTextContent(AUTHORS)

    fireEvent.click(screen.getByRole('checkbox', { name: /show unthresholded/ }))
    expect(label).toHaveTextContent('unthresholded — all values shown')
    expect(screen.getByRole('slider')).toBeDisabled()
    expect(Number(screen.getByTestId('viewer-group').getAttribute('data-cut'))).toBeLessThan(1e-6)
  })

  it('slider range is study-wide, not the selection', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('viewer-group')).toHaveTextContent('1 maps'))
    // fixture maps all have display_max 0.12
    expect(screen.getByRole('slider')).toHaveAttribute('max', '0.12')
    expect(screen.getByRole('slider')).toHaveAttribute('min', '0.001')
  })
})

describe('App footer', () => {
  it('renders data sources and licences', async () => {
    render(<App />)
    const footer = await screen.findByRole('contentinfo', { name: 'Data sources and licences' })
    expect(footer).toHaveTextContent('Fear, Anger')
    expect(footer).toHaveTextContent('GPL-3.0 (CANlab repository); article CC-BY 4.0')
    expect(footer).toHaveTextContent('Copyright (C) 1993-2004 Louis Collins')
    expect(footer).toHaveTextContent('MIT (CBIG)')
  })
})
