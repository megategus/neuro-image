import { afterEach, describe, expect, it, vi } from 'vitest'
import { loadAll } from './load'

const meta = (id: string) => ({
  id, label: id, group: 'emotion', study_id: 'wager2015', citation: 'c', doi: 'd',
  n_studies: 1, method: 'm', value_meaning: 'v', threshold: 0.001,
  threshold_type: 'display-only', threshold_label: 't', licence: 'l', caveat: 'cv',
  display_min: 0.001, display_max: 0.1, has_negative: false,
  files: { pos: `maps/${id}_pos.nii.gz`, neg: null },
})
const ids = ['anger', 'disgust', 'fear', 'happiness', 'sadness']
const profile = (id: string) => ({
  map_id: id, quantity: 'intensity_share', share: { A: 0.1 }, size_normalised: { A: 1 }, unassigned: 0.5,
})
const atlas = (displayable: boolean) => ({
  labels: { '1': { name: 'A', displayable } },
  sources: [], template: { name: 't', licence: 'l' },
})
const files = (over: Record<string, unknown> = {}): Record<string, unknown> => ({
  'maps.json': { maps: ids.map(meta), unavailable: [] },
  'profiles.json': { regions: ['A'], profiles: ids.map(profile) },
  'atlas.json': atlas(true),
  'lessons.json': { reviewed: false, lessons: [] },
  ...over,
})

function mockFetch(data: Record<string, unknown>, bad: Record<string, string> = {}) {
  const calls: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    calls.push(url)
    const name = url.split('/').pop()!
    if (bad[name] === '404') return { ok: false, status: 404, json: async () => ({}) }
    if (bad[name] === 'parse')
      return { ok: true, status: 200, json: async () => { throw new SyntaxError('bad json') } }
    return { ok: true, status: 200, json: async () => data[name] }
  }))
  return calls
}

afterEach(() => vi.unstubAllGlobals())

describe('loadAll', () => {
  it('returns 5 maps and fetches under base', async () => {
    const calls = mockFetch(files())
    const r = await loadAll('/x/')
    expect(r.maps).toHaveLength(5)
    expect(r.unavailable).toEqual([])
    expect(r.profiles).toHaveLength(5)
    expect(r.regions).toEqual(['A'])
    expect(r.lessons.reviewed).toBe(false)
    expect(r.atlas.template.licence).toBe('l')
    expect(r.atlasLabels).toBe(true)
    expect(calls).toContain('/x/data/maps.json')
  })

  it('returns unavailable entries', async () => {
    mockFetch(files({
      'maps.json': { maps: [meta('fear')], unavailable: [{ id: 'anxiety', label: 'Anxiety', reason: 'source not yet verified' }] },
    }))
    const r = await loadAll('./')
    expect(r.unavailable).toEqual([{ id: 'anxiety', label: 'Anxiety', reason: 'source not yet verified' }])
  })

  it('atlasLabels is false when no label is displayable', async () => {
    mockFetch(files({ 'atlas.json': atlas(false) }))
    expect((await loadAll('./')).atlasLabels).toBe(false)
  })

  it('rejects naming the file on a non-OK response', async () => {
    mockFetch(files(), { 'profiles.json': '404' })
    await expect(loadAll('./')).rejects.toThrow(/profiles\.json/)
  })

  it('rejects naming the file on a JSON parse error', async () => {
    mockFetch(files(), { 'lessons.json': 'parse' })
    await expect(loadAll('./')).rejects.toThrow(/lessons\.json/)
  })
})
