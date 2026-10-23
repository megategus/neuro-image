import { useEffect, useMemo, useState } from 'react'
import { loadAll, type LoadedData } from './data/load'
import BrainViewer from './viewer/BrainViewer'
import InfoPanel from './panels/InfoPanel'
import ProfileChart, { type ProfileMode } from './panels/ProfileChart'
import LessonPlayer, { type LessonView } from './lessons/LessonPlayer'
import './App.css'

const UNTHRESHOLDED = 1e-9

export default function App() {
  const [data, setData] = useState<LoadedData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [cut, setCut] = useState<number | null>(null)
  const [unthresholded, setUnthresholded] = useState(false)
  const [showLabels, setShowLabels] = useState(false)
  const [mode, setMode] = useState<ProfileMode>('share')
  const [guided, setGuided] = useState(true)
  const [lessonView, setLessonView] = useState<LessonView>('both')
  const [lessonIndex, setLessonIndex] = useState(0)
  const availableIds = data ? data.maps.map((m) => m.id) : []

  useEffect(() => {
    loadAll().then(setData).catch((e: Error) => setError(e.message))
  }, [])

  const maps = useMemo(
    () => (data ? selected.map((id) => data.maps.find((m) => m.id === id)!).filter(Boolean) : []),
    [data, selected],
  )

  if (error) return <p role="alert">Could not load data: {error}</p>
  if (!data) return <p>Loading…</p>

  const profiles = data.profiles.filter((p) => selected.includes(p.map_id))
  const labels = Object.fromEntries(data.maps.map((m) => [m.id, m.label]))
  const wagerMaps = maps.filter((m) => m.study_id === 'wager2015')
  const sliderMax = Math.max(0.001, ...wagerMaps.map((m) => m.display_max))
  const effectiveCut = unthresholded ? UNTHRESHOLDED : cut

  const showOverlay = !guided || lessonView !== 'profile'
  const showProfile = !guided || lessonView !== 'overlay'

  const loadMaps = (ids: string[], view: LessonView) => {
    setSelected(ids.filter((id) => availableIds.includes(id)))
    setLessonView(view)
  }

  const toggle = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))

  return (
    <div className="app">
      <header>
        <h1>Brain Condition Atlas</h1>
      </header>
      <aside className="picker">
        <h2>Conditions</h2>
        <ul>
          {data.maps.map((m) => (
            <li key={m.id}>
              <label>
                <input type="checkbox" checked={selected.includes(m.id)} onChange={() => toggle(m.id)} />{' '}
                {m.label}
              </label>
            </li>
          ))}
          {data.unavailable.map((u) => (
            <li key={u.id} className="unavailable">
              <label>
                <input type="checkbox" disabled /> {u.label}
              </label>{' '}
              <span className="reason">not yet available: {u.reason}</span>
            </li>
          ))}
        </ul>
        <div className="controls">
          {wagerMaps.length > 0 && (
            <>
          <label className="slider">
            Display cut: {effectiveCut === null ? 'default' : unthresholded ? 'none' : cut}
            <input
              type="range"
              min={0.001}
              max={sliderMax}
              step={0.001}
              value={cut ?? 0.001}
              disabled={unthresholded}
              onChange={(e) => setCut(Number(e.target.value))}
            />
          </label>
          {wagerMaps[0] && <p className="threshold-label">{wagerMaps[0].threshold_label}</p>}
          <label>
            <input type="checkbox" checked={unthresholded} onChange={(e) => setUnthresholded(e.target.checked)} /> show
            unthresholded
          </label>
            </>
          )}
          {data.atlasLabels && (
            <label>
              <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} /> region
              labels
            </label>
          )}
        </div>
      </aside>
      <main className="viewer">
        {guided ? (
          <LessonPlayer
            lessons={data.lessons}
            unavailableIds={data.unavailable.map((u) => u.id)}
            initialIndex={lessonIndex}
            onIndexChange={setLessonIndex}
            onLoadMaps={loadMaps}
            onExit={() => setGuided(false)}
          />
        ) : (
          <button onClick={() => setGuided(true)}>Guided lessons</button>
        )}
        {showOverlay && (
          <BrainViewer maps={maps} cut={effectiveCut} showLabels={showLabels && data.atlasLabels} atlas={data.atlas} />
        )}
      </main>
      <section className="details">
        {showOverlay && maps.map((m) => (
          <InfoPanel key={m.id} map={m} />
        ))}
        {showProfile && profiles.length > 0 && (
          <div>
            <h2>Network profile</h2>
            <div role="group" aria-label="Profile mode" className="mode-toggle">
              <button aria-pressed={mode === 'share'} onClick={() => setMode('share')}>
                Share of evidence
              </button>
              <button aria-pressed={mode === 'size_normalised'} onClick={() => setMode('size_normalised')}>
                Relative to region size
              </button>
            </div>
            <ProfileChart profiles={profiles} regions={data.regions} mode={mode} labels={labels} />
          </div>
        )}
      </section>
    </div>
  )
}
