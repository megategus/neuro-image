import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureMap } from './testFixtures'

vi.mock('./viewer/BrainViewer', () => ({
  default: ({ maps }: { maps: unknown[] }) => <div data-testid="viewer-group">{maps.length} maps</div>,
}))
vi.mock('./data/load', () => ({
  loadAll: async () => ({
    maps: [fixtureMap({ id: 'fear', label: 'Fear' }), fixtureMap({ id: 'anger', label: 'Anger' })],
    unavailable: [{ id: 'anxiety', label: 'Anxiety', reason: 'source not yet verified' }],
    profiles: [], regions: [], atlas: { labels: {} }, atlasLabels: false,
    lessons: {
      reviewed: true,
      lessons: [
        { id: 'a', title: 'One', map_ids: ['fear'], view: 'overlay', body: ['x'], notice: 'n', claims: [] },
        { id: 'b', title: 'Two', map_ids: ['anger', 'fear'], view: 'both', body: ['x'], notice: 'n', claims: [] },
        { id: 'c', title: 'Three', map_ids: ['fear', 'anxiety'], view: 'both', body: ['x'], notice: 'n', claims: [] },
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
