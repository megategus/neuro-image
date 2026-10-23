import type { MapMeta } from './data/types'

export function fixtureMap(over: Partial<MapMeta> = {}): MapMeta {
  return {
    id: 'fear',
    label: 'Fear',
    group: 'emotion',
    study_id: 'wager2015',
    citation: 'Wager TD et al (2015). A Bayesian model of category-specific emotional brain responses.',
    doi: '10.1371/journal.pcbi.1004066',
    n_studies: 148,
    method: 'Bayesian spatial point process (BSPP) coordinate-based meta-analysis',
    value_meaning: 'posterior expected number of activation centres',
    threshold: 0.001,
    threshold_type: 'display-only',
    threshold_label: 'display threshold chosen by the authors — not a significance test',
    licence: 'GPL-3.0 (CANlab repository); article CC-BY 4.0',
    caveat: 'Example caveat',
    caveat_reviewed: false,
    display_min: 0.001,
    display_max: 0.12,
    has_negative: false,
    files: { pos: 'maps/fear_pos.nii.gz', neg: null },
    ...over,
  }
}
