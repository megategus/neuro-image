import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ProfileChart from './ProfileChart'
import type { Profile } from '../data/types'

const regions = ['Visual', 'Amygdala']
const mk = (id: string): Profile => ({
  map_id: id,
  quantity: 'intensity_share',
  share: { Visual: 0.3, Amygdala: 0.2 },
  size_normalised: { Visual: 0.5, Amygdala: 2 },
  unassigned: 0.5,
})

describe('ProfileChart', () => {
  it('renders the note and one bar per map and row (regions plus unassigned)', () => {
    render(<ProfileChart profiles={[mk('fear'), mk('anger')]} regions={regions} mode="share" />)
    expect(
      screen.getByText("Compares where each condition's evidence lies, not how strong it is."),
    ).toBeInTheDocument()
    expect(screen.getAllByTestId('profile-bar')).toHaveLength(6)
    expect(screen.getByText('Unassigned (outside atlas regions)')).toBeInTheDocument()
  })

  it('omits unassigned row in size-normalised mode', () => {
    render(<ProfileChart profiles={[mk('fear')]} regions={regions} mode="size_normalised" />)
    expect(screen.queryByText(/Unassigned/)).toBeNull()
    expect(screen.getAllByTestId('profile-bar')).toHaveLength(2)
  })
})
