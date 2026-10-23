export type ThresholdType = 'statistical' | 'display-only' | 'none'

export interface MapMeta {
  id: string
  label: string
  group: string
  study_id: string
  citation: string
  doi: string
  n_studies: number
  method: string
  value_meaning: string
  threshold: number | null
  threshold_type: ThresholdType
  threshold_label: string
  licence: string
  caveat: string
  display_min: number
  display_max: number
  has_negative: boolean
  files: { pos: string; neg: string | null }
}

export interface UnavailableMap {
  id: string
  label: string
  reason: string
}

export interface MapsFile {
  maps: MapMeta[]
  unavailable: UnavailableMap[]
}

export interface Profile {
  map_id: string
  quantity: string
  share: Record<string, number>
  size_normalised: Record<string, number>
  unassigned: number
}

export interface ProfilesFile {
  regions: string[]
  profiles: Profile[]
}

export interface AtlasLabel {
  name: string
  displayable: boolean
}

export interface AtlasSource {
  name: string
  citation: string
  licence: string
  bundled: boolean
}

export interface AtlasFile {
  labels: Record<string, AtlasLabel>
  sources: AtlasSource[]
  template: { name: string; licence: string }
}

export interface Claim {
  text: string
  source_doi: string
}

export interface Lesson {
  id: string
  title: string
  map_ids: string[]
  view: 'overlay' | 'profile' | 'both'
  body: string[]
  notice: string
  claims: Claim[]
}

export interface LessonsFile {
  reviewed: boolean
  lessons: Lesson[]
}
