import type { MapMeta } from './types'

export type ScaleGroup = { studyId: string; mapIds: string[]; min: number; max: number }

// Maps may share a colour scale only when they come from the same study.
// Groups appear in the order their study_id first occurs in `selected`;
// mapIds keep selection order within each group.
export function groupScales(selected: MapMeta[]): ScaleGroup[] {
  const byStudy = new Map<string, ScaleGroup>()
  for (const m of selected) {
    const existing = byStudy.get(m.study_id)
    if (existing) {
      existing.mapIds.push(m.id)
      existing.min = Math.min(existing.min, m.display_min)
      existing.max = Math.max(existing.max, m.display_max)
    } else {
      byStudy.set(m.study_id, {
        studyId: m.study_id,
        mapIds: [m.id],
        min: m.display_min,
        max: m.display_max,
      })
    }
  }
  return [...byStudy.values()]
}

// True only when every selected map shares one study_id. An empty selection cannot overlay.
export function canOverlay(selected: MapMeta[]): boolean {
  if (selected.length === 0) return false
  return groupScales(selected).length === 1
}
