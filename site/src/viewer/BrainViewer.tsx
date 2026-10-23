import { useEffect, useMemo, useRef, useState } from 'react'
import { Niivue, SHOW_RENDER } from '@niivue/niivue'
import type { AtlasFile, MapMeta } from '../data/types'
import { groupScales, type ScaleGroup } from '../data/scales'
import { colormapGradient } from './colourbar'

export const WEBGL2_MESSAGE =
  '3D view needs WebGL2, which this browser does not provide. The map details and network profiles below still work.'

const WARM = 'warm'
const COOL = 'winter'

interface Props {
  maps: MapMeta[]
  // Every published map; a study's colour range spans all of its maps, not just the selection.
  allMaps?: MapMeta[]
  cut: number | null
  showLabels: boolean
  atlas?: AtlasFile
  dataBase?: string
}

function hasWebGL2(): boolean {
  try {
    return document.createElement('canvas').getContext('webgl2') !== null
  } catch {
    return false
  }
}

// Canvases of one viewer group share crosshair, slice position and 3D view:
// each instance broadcasts to the others (NiiVue only sends from the focused canvas).
type SyncSet = Set<Niivue>
const SYNC_OPTS = { '2d': true, '3d': true }

function relink(set: SyncSet) {
  for (const nv of set) {
    try {
      nv.broadcastTo([...set].filter((o) => o !== nv), SYNC_OPTS)
    } catch {
      /* sync is a convenience; never break drawing */
    }
  }
}

interface CanvasProps {
  map: MapMeta
  group: ScaleGroup
  sync: SyncSet
  calMin: number
  showLabels: boolean
  atlas?: AtlasFile
  dataBase: string
}

function MapCanvas({ map, group, sync, calMin, showLabels, atlas, dataBase }: CanvasProps) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const nvRef = useRef<Niivue | null>(null)
  const loadedRef = useRef(false)
  const labelIdx = useRef(-1)
  const calRef = useRef({ min: calMin, max: group.max })
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [region, setRegion] = useState<string | null>(null)

  // Push the current cal_min/cal_max onto the already-loaded overlays (indices 1, and 2 if negative).
  const applyCal = () => {
    const nv = nvRef.current
    if (!nv || !loadedRef.current) return
    const overlays = map.files.neg ? [1, 2] : [1]
    for (const i of overlays) {
      const v = nv.volumes[i]
      if (!v) continue
      v.cal_min = calRef.current.min
      v.cal_max = calRef.current.max
    }
    nv.updateGLVolume()
  }

  // One Niivue instance per mounted canvas; the canvas is created here so a
  // torn-down (lost) context is never reused, e.g. by StrictMode's double mount.
  useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return
    const canvas = document.createElement('canvas')
    canvas.className = 'brain-canvas'
    canvas.setAttribute('aria-label', `Brain view: ${map.label}`)
    wrap.appendChild(canvas)
    let cancelled = false
    let nv: Niivue | null = null
    const teardown = () => {
      if (!nv) return
      const inst = nv
      nv = null
      if (nvRef.current === inst) nvRef.current = null
      loadedRef.current = false
      if (sync.delete(inst)) relink(sync)
      try {
        inst.cleanup()
      } catch {
        /* ignore */
      }
      try {
        inst.gl?.getExtension('WEBGL_lose_context')?.loseContext()
      } catch {
        /* ignore */
      }
    }
    ;(async () => {
      try {
        nv = new Niivue({
          isColorbar: false,
          multiplanarShowRender: SHOW_RENDER.ALWAYS,
          backColor: [0.05, 0.05, 0.08, 1],
          show3Dcrosshair: true,
        })
        const inst = nv
        await inst.attachToCanvas(canvas)
        if (cancelled) return teardown()
        nvRef.current = inst
        sync.add(inst)
        relink(sync)
        setReady(true)
      } catch (e) {
        if (cancelled) return teardown()
        setError((e as Error).message)
      }
    })()
    return () => {
      cancelled = true
      setReady(false)
      teardown()
      canvas.remove()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Load volumes only when the map, labels or atlas change; never on cut changes.
  useEffect(() => {
    const nv = nvRef.current
    if (!nv || !ready) return
    let cancelled = false
    loadedRef.current = false
    const { min, max } = calRef.current
    const list: Record<string, unknown>[] = [
      { url: `${dataBase}template.nii.gz`, colormap: 'gray', opacity: 1 },
      { url: `${dataBase}${map.files.pos}`, colormap: WARM, cal_min: min, cal_max: max, opacity: 1 },
    ]
    if (map.files.neg) {
      list.push({ url: `${dataBase}${map.files.neg}`, colormap: COOL, cal_min: min, cal_max: max, opacity: 1 })
    }
    labelIdx.current = -1
    if (showLabels) {
      labelIdx.current = list.length
      list.push({ url: `${dataBase}atlas_labels.nii.gz`, colormap: 'random', opacity: 0.3, cal_min: 0.5 })
    }
    nv.onLocationChange = (loc: unknown) => {
      if (labelIdx.current < 0) {
        setRegion(null)
        return
      }
      const values = (loc as { values?: { value: number }[] }).values
      const v = values?.[labelIdx.current]?.value
      const entry = v ? atlas?.labels[String(Math.round(v))] : undefined
      setRegion(entry && entry.displayable ? entry.name : null)
    }
    nv.loadVolumes(list as never)
      .then(() => {
        if (cancelled) return
        loadedRef.current = true
        nv.setSliceType(nv.sliceTypeMultiplanar)
        try {
          // Start at the volume centre, not on any structure or peak, so no map is
          // framed around one region. A canvas added to a group joins its peers'
          // current position instead, so the group stays in step.
          const peer = [...sync].find((o) => o !== nv && o.volumes.length > 0)
          nv.scene.crosshairPos = peer ? nv.mm2frac(peer.frac2mm(peer.scene.crosshairPos)) : [0.5, 0.5, 0.5]
          nv.drawScene()
        } catch {
          /* cosmetic only */
        }
        applyCal()
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, map.id, showLabels, atlas, dataBase])

  // Cut changes mutate the loaded overlay in place.
  useEffect(() => {
    calRef.current = { min: calMin, max: group.max }
    applyCal()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calMin, group.max])

  return (
    <figure className="viewer-cell">
      <figcaption>{map.label}</figcaption>
      <div className="canvas-wrap" ref={wrapRef} />
      {error && <p className="viewer-error">Could not draw this map: {error}</p>}
      {showLabels && <p className="region-readout">Region under cursor: {region ?? 'none shown'}</p>}
    </figure>
  )
}

export default function BrainViewer({
  maps,
  allMaps,
  cut,
  showLabels,
  atlas,
  dataBase = `${import.meta.env.BASE_URL}data/`,
}: Props) {
  const webgl2 = useMemo(() => hasWebGL2(), [])
  const groups = useMemo(() => groupScales(maps, allMaps ?? maps), [maps, allMaps])
  // One stable sync set per study, kept for the life of the viewer.
  const [syncSets] = useState(() => new Map<string, SyncSet>())
  const syncFor = (studyId: string) => {
    let set = syncSets.get(studyId)
    if (!set) {
      set = new Set()
      syncSets.set(studyId, set)
    }
    return set
  }
  const warm = useMemo(() => colormapGradient(WARM), [])
  const cool = useMemo(() => colormapGradient(COOL), [])

  if (!webgl2) return <p className="webgl-message" role="status">{WEBGL2_MESSAGE}</p>
  if (maps.length === 0) return <p className="viewer-empty">Pick a condition to see its map.</p>

  return (
    <div className="viewer-groups">
      {groups.map((g) => {
        const gm = g.mapIds.map((id) => maps.find((m) => m.id === id)!)
        // The cut slider only governs the Wager group; other studies use their own display range.
        const calMin = g.studyId === 'wager2015' && cut !== null ? cut : g.min
        const first = gm[0]
        return (
          <section className="viewer-group" data-testid="viewer-group" key={g.studyId}>
            <div className="viewer-grid">
              {gm.map((m) => (
                <MapCanvas key={m.id} map={m} group={g} sync={syncFor(g.studyId)} calMin={calMin} showLabels={showLabels} atlas={atlas} dataBase={dataBase} />
              ))}
            </div>
            {g.studyId !== 'wager2015' && <p className="group-threshold">{first.threshold_label}</p>}
            <div className="colourbar">
              <div className="colourbar-label">
                {first.value_meaning} — {first.citation.split('(')[0].trim()} ({g.studyId})
              </div>
              <div className="colourbar-gradient warm" data-testid="colourbar-warm" style={{ background: warm }} />
              <div className="colourbar-ticks">
                <span>{calMin <= 1e-6 ? '> 0' : calMin}</span>
                <span>{g.max}</span>
              </div>
              {gm.some((m) => m.files.neg) && (
                <>
                  <div className="colourbar-gradient cool" data-testid="colourbar-cool" style={{ background: cool }} />
                  <div className="colourbar-ticks"><span>decreases</span></div>
                </>
              )}
            </div>
            {showLabels && <p className="label-note">Subcortical labels not shown (atlas licence)</p>}
          </section>
        )
      })}
    </div>
  )
}
