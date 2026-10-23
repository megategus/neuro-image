import type {
  AtlasFile, LessonsFile, MapMeta, MapsFile, Profile, ProfilesFile, UnavailableMap,
} from './types'

export interface LoadedData {
  maps: MapMeta[]
  unavailable: UnavailableMap[]
  profiles: Profile[]
  regions: string[]
  lessons: LessonsFile
  atlas: AtlasFile
  atlasLabels: boolean
}

async function getJson<T>(base: string, name: string): Promise<T> {
  const url = `${base}data/${name}`
  let res: Response
  try {
    res = await fetch(url)
  } catch (e) {
    throw new Error(`Failed to fetch ${name}: ${(e as Error).message}`)
  }
  if (!res.ok) throw new Error(`Failed to load ${name}: HTTP ${res.status}`)
  try {
    return (await res.json()) as T
  } catch (e) {
    throw new Error(`Failed to parse ${name}: ${(e as Error).message}`)
  }
}

export async function loadAll(base: string = import.meta.env.BASE_URL): Promise<LoadedData> {
  const [maps, profiles, atlas, lessons] = await Promise.all([
    getJson<MapsFile>(base, 'maps.json'),
    getJson<ProfilesFile>(base, 'profiles.json'),
    getJson<AtlasFile>(base, 'atlas.json'),
    getJson<LessonsFile>(base, 'lessons.json'),
  ])
  return {
    maps: maps.maps,
    unavailable: maps.unavailable ?? [],
    profiles: profiles.profiles,
    regions: profiles.regions,
    lessons,
    atlas,
    atlasLabels: Object.values(atlas.labels).some((l) => l.displayable),
  }
}
