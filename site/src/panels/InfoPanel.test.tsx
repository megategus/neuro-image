import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import InfoPanel from './InfoPanel'
import { fixtureMap } from '../testFixtures'

describe('InfoPanel', () => {
  it('renders the DOI link and verbatim threshold label', () => {
    render(<InfoPanel map={fixtureMap()} />)
    const link = screen.getByRole('link', { name: /10\.1371\/journal\.pcbi\.1004066/ })
    expect(link).toHaveAttribute('href', 'https://doi.org/10.1371/journal.pcbi.1004066')
    expect(
      screen.getByText('display threshold chosen by the authors — not a significance test'),
    ).toBeInTheDocument()
    expect(screen.getByText(/posterior expected number of activation centres/)).toBeInTheDocument()
    expect(screen.getByText(/148/)).toBeInTheDocument()
  })

  it('shows the no-decreases note only for wager2015', () => {
    const { rerender } = render(<InfoPanel map={fixtureMap()} />)
    expect(screen.getByText('No decreases can appear in this map by method')).toBeInTheDocument()
    rerender(<InfoPanel map={fixtureMap({ study_id: 'other', id: 'x' })} />)
    expect(screen.queryByText(/No decreases can appear/)).toBeNull()
  })
})
