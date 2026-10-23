import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SiteFooter from './SiteFooter'
import { fixtureMap } from '../testFixtures'
import type { AtlasFile } from '../data/types'

const atlas: AtlasFile = {
  labels: {},
  template: { name: 'MNI ICBM152 2009', licence: 'MNI ICBM152 licence: Copyright (C) 1993-2004 Louis Collins' },
  sources: [
    { name: 'Yeo 2011', citation: 'Yeo et al.', licence: 'MIT (CBIG); Copyright (c) 2016 CBIG', bundled: true },
    { name: 'Harvard–Oxford subcortical', citation: 'Desikan', licence: 'FSL licence', bundled: false },
  ],
}

describe('SiteFooter', () => {
  it('lists map, template and atlas licences, notices, repository and GPL links', () => {
    render(<SiteFooter maps={[fixtureMap(), fixtureMap({ id: 'anger', label: 'Anger' })]} atlas={atlas} dataBase="/d/" />)
    expect(screen.getByText('Fear, Anger')).toBeInTheDocument()
    expect(screen.getByText(/GPL-3\.0 \(CANlab repository\); article CC-BY 4\.0/)).toBeInTheDocument()
    expect(screen.getByText(/Copyright \(C\) 1993-2004 Louis Collins/)).toBeInTheDocument()
    expect(screen.getByText(/MIT \(CBIG\); Copyright \(c\) 2016 CBIG/)).toBeInTheDocument()
    expect(screen.getByText(/FSL licence\. Used to compute network profiles only; not distributed\./)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'NOTICES.txt' })).toHaveAttribute('href', '/d/NOTICES.txt')
    expect(screen.getByRole('link', { name: 'github.com/megategus/neuro-image' }))
      .toHaveAttribute('href', 'https://github.com/megategus/neuro-image')
    expect(screen.getByRole('link', { name: /GNU General Public License v3\.0/ }))
      .toHaveAttribute('href', 'https://www.gnu.org/licenses/gpl-3.0.html')
  })
})
