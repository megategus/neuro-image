import type { MapMeta } from './types'

export type ScaleGroup = { studyId: string; mapIds: string[]; min: number; max: number }

// Maps may share a colour scale only when they come from the same study.
// Groups appear in the order their study_id first occurs in `selected`;
// mapIds keep selection order within each group.
// The range of a group spans every map of that study in `allMaps` (the full
// map list), not just the selected ones, so a map's colours never change when
// other maps of its study are added or removed.
export function groupScales(selected: MapMeta[], allMaps: MapMeta[] = selected): ScaleGroup[] {
  const byStudy = new Map<string, ScaleGroup>()
  for (const m of selected) {
    const existing = byStudy.get(m.study_id)
    if (existing) {
      existing.mapIds.push(m.id)
    } else {
      byStudy.set(m.study_id, { studyId: m.study_id, mapIds: [m.id], min: Infinity, max: -Infinity })
    }
  }
  const pool = [...allMaps, ...selected]
  for (const g of byStudy.values()) {
    for (const m of pool) {
      if (m.study_id !== g.studyId) continue
      g.min = Math.min(g.min, m.display_min)
      g.max = Math.max(g.max, m.display_max)
    }
  }
  return [...byStudy.values()]
}

// Study-wide display range for one study (e.g. the slider's upper bound).
export function studyRange(allMaps: MapMeta[], studyId: string): { min: number; max: number } | null {
  const ms = allMaps.filter((m) => m.study_id === studyId)
  if (ms.length === 0) return null
  return { min: Math.min(...ms.map((m) => m.display_min)), max: Math.max(...ms.map((m) => m.display_max)) }
}
