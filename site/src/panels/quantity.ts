import type { MapMeta, Profile } from '../data/types'

// Which quantity a profile's bars measure (spec 8.2: intensity share is allowed only if labelled).
export function quantityLabel(p: Profile, map?: MapMeta): string {
  if (p.quantity === 'voxel_share') {
    return `share of suprathreshold voxels (statistical threshold ${map?.threshold ?? 'stated by the authors'})`
  }
  if (map?.threshold_type === 'display-only') {
    return "share of total map intensity (all positive values; the display cut is not applied)"
  }
  return 'share of total map intensity (unthresholded)'
}
