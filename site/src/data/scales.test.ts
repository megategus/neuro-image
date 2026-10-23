import { describe, expect, it } from 'vitest'
import { groupScales, studyRange } from './scales'
import type { MapMeta } from './types'

const base: MapMeta = {
  id: '', label: '', group: 'emotion', study_id: 'wager2015', citation: 'c', doi: 'd',
  n_studies: 1, method: 'm', value_meaning: 'v', threshold: 0.001,
  threshold_type: 'display-only', threshold_label: 't', licence: 'l', caveat: 'cv', caveat_reviewed: false,
  display_min: 0.001, display_max: 0.1, has_negative: false,
  files: { pos: '', neg: null },
}

const map = (id: string, study_id: string, display_min: number, display_max: number): MapMeta => ({
  ...base, id, label: id, study_id, display_min, display_max,
  files: { pos: `maps/${id}_pos.nii.gz`, neg: null },
})

describe('groupScales', () => {
  it('fear+sadness (same study) -> one group with a shared range', () => {
    const groups = groupScales([
      map('fear', 'wager2015', 0.002, 0.2),
      map('sadness', 'wager2015', 0.001, 0.5),
    ])
    expect(groups).toEqual([
      { studyId: 'wager2015', mapIds: ['fear', 'sadness'], min: 0.001, max: 0.5 },
    ])
  })

  it('fear+retrieval (different studies) -> two groups', () => {
    const selected = [
      map('fear', 'wager2015', 0.002, 0.2),
      map('retrieval', 'neurosynth2011', 0.01, 0.8),
    ]
    const groups = groupScales(selected)
    expect(groups).toHaveLength(2)
    expect(groups.map((g) => g.studyId)).toEqual(['wager2015', 'neurosynth2011'])
    expect(groups[0]).toEqual({ studyId: 'wager2015', mapIds: ['fear'], min: 0.002, max: 0.2 })
    expect(groups[1]).toEqual({ studyId: 'neurosynth2011', mapIds: ['retrieval'], min: 0.01, max: 0.8 })
  })

  it('single map -> one group equal to its own range', () => {
    const groups = groupScales([map('fear', 'wager2015', 0.002, 0.2)])
    expect(groups).toEqual([
      { studyId: 'wager2015', mapIds: ['fear'], min: 0.002, max: 0.2 },
    ])
  })

  it('orders groups by first appearance of study_id in the selection, keeping selection order within a group', () => {
    const groups = groupScales([
      map('retrieval', 'neurosynth2011', 0.01, 0.8),
      map('fear', 'wager2015', 0.002, 0.2),
      map('sadness', 'wager2015', 0.001, 0.5),
      map('memory', 'neurosynth2011', 0.02, 0.4),
    ])
    expect(groups.map((g) => g.studyId)).toEqual(['neurosynth2011', 'wager2015'])
    expect(groups[0].mapIds).toEqual(['retrieval', 'memory'])
    expect(groups[1].mapIds).toEqual(['fear', 'sadness'])
  })

  it('empty selection -> no groups', () => {
    expect(groupScales([])).toEqual([])
  })
})

describe('study-wide range', () => {
  const all = [
    map('fear', 'wager2015', 0.001, 0.0877),
    map('anger', 'wager2015', 0.001, 0.1207),
    map('sadness', 'wager2015', 0.001, 0.09),
    map('retrieval', 'other', 0.5, 3),
  ]

  it('uses every map of the study, not just the selection', () => {
    expect(groupScales([all[0]], all)).toEqual([
      { studyId: 'wager2015', mapIds: ['fear'], min: 0.001, max: 0.1207 },
    ])
  })

  it("fear's range does not change when sadness or anger is added", () => {
    const alone = groupScales([all[0]], all)[0]
    const withSad = groupScales([all[0], all[2]], all)[0]
    const withAll = groupScales([all[0], all[1], all[2]], all)[0]
    expect(withSad.max).toBe(alone.max)
    expect(withAll.max).toBe(alone.max)
    expect(withSad.min).toBe(alone.min)
  })

  it('never mixes ranges across studies', () => {
    const groups = groupScales([all[0], all[3]], all)
    expect(groups[0].max).toBe(0.1207)
    expect(groups[1]).toEqual({ studyId: 'other', mapIds: ['retrieval'], min: 0.5, max: 3 })
  })

  it('studyRange gives the study-wide range or null', () => {
    expect(studyRange(all, 'wager2015')).toEqual({ min: 0.001, max: 0.1207 })
    expect(studyRange(all, 'none')).toBeNull()
  })
})
