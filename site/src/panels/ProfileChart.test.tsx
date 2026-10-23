import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ProfileChart from './ProfileChart'
import { fixtureMap } from '../testFixtures'
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

  it('labels the quantity of each profile in the legend', () => {
    const stat: Profile = { ...mk('retrieval'), quantity: 'voxel_share' }
    const maps = [
      fixtureMap(),
      fixtureMap({ id: 'retrieval', label: 'Retrieval', study_id: 'other', threshold: 3.1, threshold_type: 'statistical' }),
      fixtureMap({ id: 'anx', label: 'Anxiety', study_id: 'x', threshold: null, threshold_type: 'none' }),
    ]
    render(<ProfileChart profiles={[mk('fear'), stat, mk('anx')]} regions={regions} mode="share"
      labels={{ fear: 'Fear', retrieval: 'Retrieval', anx: 'Anxiety' }} maps={maps} />)
    const legend = screen.getAllByRole('listitem').map((li) => li.textContent?.trim())
    expect(legend[0]).toBe('Fear — share of total map intensity (all positive values; the display cut is not applied)')
    expect(legend[1]).toBe('Retrieval — share of suprathreshold voxels (statistical threshold 3.1)')
    expect(legend[2]).toBe('Anxiety — share of total map intensity (unthresholded)')
  })
})
