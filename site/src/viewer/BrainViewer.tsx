import { useEffect, useMemo, useRef, useState } from 'react'
import { Niivue, SHOW_RENDER } from '@niivue/niivue'
import type { AtlasFile, MapMeta } from '../data/types'
import { groupScales, type ScaleGroup } from '../data/scales'

export const WEBGL2_MESSAGE =
  '3D view needs WebGL2, which this browser does not provide. The map details and network profiles below still work.'

const WARM = 'warm'
const COOL = 'winter'

interface Props {
  maps: MapMeta[]
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

interface CanvasProps {
  map: MapMeta
  group: ScaleGroup
  calMin: number
  showLabels: boolean
  atlas?: AtlasFile
  dataBase: string
}

function MapCanvas({ map, group, calMin, showLabels, atlas, dataBase }: CanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const nvRef = useRef<Niivue | null>(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [region, setRegion] = useState<string | null>(null)
  const labelIdx = useRef(-1)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    let nv: Niivue
    try {
      nv = new Niivue({
        isColorbar: false,
        multiplanarShowRender: SHOW_RENDER.ALWAYS,
        backColor: [0.05, 0.05, 0.08, 1],
        show3Dcrosshair: true,
      })
    } catch (e) {
      setError((e as Error).message)
      return
    }
    nvRef.current = nv
    let cancelled = false
    nv.attachToCanvas(canvas)
      .then(() => {
        if (!cancelled) setReady(true)
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message)
      })
    return () => {
      cancelled = true
      nvRef.current = null
      try {
        nv.cleanup()
      } catch {
        /* ignore */
      }
    }
  }, [])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || !ready) return
    let cancelled = false
    const list: Record<string, unknown>[] = [
      { url: `${dataBase}template.nii.gz`, colormap: 'gray', opacity: 1 },
      {
        url: `${dataBase}${map.files.pos}`,
        colormap: WARM,
        cal_min: calMin,
        cal_max: group.max,
        opacity: 1,
      },
    ]
    if (map.files.neg) {
      list.push({
        url: `${dataBase}${map.files.neg}`,
        colormap: COOL,
        cal_min: calMin,
        cal_max: group.max,
        opacity: 1,
      })
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
        nv.setSliceType(nv.sliceTypeMultiplanar)
        try {
          // Start with the crosshair near the right amygdala (MNI 22, -4, -12).
          nv.scene.crosshairPos = nv.mm2frac([22, -4, -12])
          nv.drawScene()
        } catch {
          /* cosmetic only */
        }
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message)
      })
    return () => {
      cancelled = true
    }
  }, [ready, map, group.max, calMin, showLabels, atlas, dataBase])

  return (
    <figure className="viewer-cell">
      <figcaption>{map.label}</figcaption>
      <div className="canvas-wrap">
        <canvas ref={canvasRef} className="brain-canvas" aria-label={`Brain view: ${map.label}`} />
      </div>
      {error && <p className="viewer-error">Could not draw this map: {error}</p>}
      {showLabels && <p className="region-readout">Region under cursor: {region ?? 'none shown'}</p>}
    </figure>
  )
}

export default function BrainViewer({
  maps,
  cut,
  showLabels,
  atlas,
  dataBase = `${import.meta.env.BASE_URL}data/`,
}: Props) {
  const webgl2 = useMemo(() => hasWebGL2(), [])
  const groups = useMemo(() => groupScales(maps), [maps])

  if (!webgl2) return <p className="webgl-message" role="status">{WEBGL2_MESSAGE}</p>
  if (maps.length === 0) return <p className="viewer-empty">Pick a condition to see its map.</p>

  return (
    <div className="viewer-groups">
      {groups.map((g) => {
        const gm = g.mapIds.map((id) => maps.find((m) => m.id === id)!)
        const calMin = cut === null ? g.min : cut
        const first = gm[0]
        return (
          <section className="viewer-group" data-testid="viewer-group" key={g.studyId}>
            <div className="viewer-grid">
              {gm.map((m) => (
                <MapCanvas key={m.id} map={m} group={g} calMin={calMin} showLabels={showLabels} atlas={atlas} dataBase={dataBase} />
              ))}
            </div>
            <div className="colourbar">
              <div className="colourbar-label">
                {first.value_meaning} — {first.citation.split('(')[0].trim()} ({g.studyId})
              </div>
              <div className="colourbar-gradient warm" />
              <div className="colourbar-ticks">
                <span>{calMin}</span>
                <span>{g.max}</span>
              </div>
              {gm.some((m) => m.files.neg) && (
                <>
                  <div className="colourbar-gradient cool" />
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
