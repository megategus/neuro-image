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

  it('shows group, study and decreases-present rows', () => {
    render(<InfoPanel map={fixtureMap()} />)
    expect(screen.getByText('Group')).toBeInTheDocument()
    expect(screen.getByText('emotion')).toBeInTheDocument()
    expect(screen.getByText('Study')).toBeInTheDocument()
    expect(screen.getByText('Decreases present')).toBeInTheDocument()
    expect(screen.getByText('no')).toBeInTheDocument()
  })

  it('shows the no-decreases note only for wager2015', () => {
    const { rerender } = render(<InfoPanel map={fixtureMap()} />)
    expect(screen.getByText('No decreases can appear in this map by method')).toBeInTheDocument()
    rerender(<InfoPanel map={fixtureMap({ study_id: 'other', id: 'x' })} />)
    expect(screen.queryByText(/No decreases can appear/)).toBeNull()
  })

  it('flags an unreviewed caveat, and not a reviewed one', () => {
    const { rerender } = render(<InfoPanel map={fixtureMap()} />)
    expect(screen.getByText('Caveat not yet medically reviewed')).toBeInTheDocument()
    rerender(<InfoPanel map={fixtureMap({ caveat_reviewed: true })} />)
    expect(screen.queryByText('Caveat not yet medically reviewed')).toBeNull()
    expect(screen.getByText('Example caveat')).toBeInTheDocument()
  })

  it('labels the Wager study count as the whole model', () => {
    render(<InfoPanel map={fixtureMap()} />)
    expect(screen.getByText('Studies in model (all five emotions)')).toBeInTheDocument()
  })
})
