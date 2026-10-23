import type { MapMeta, Profile } from '../data/types'
import { quantityLabel } from './quantity'
import { mapColour } from './palette'

export type ProfileMode = 'share' | 'size_normalised'

interface Props {
  profiles: Profile[]
  regions: string[]
  mode: ProfileMode
  labels?: Record<string, string>
  maps?: MapMeta[]
}

export default function ProfileChart({ profiles, regions, mode, labels = {}, maps = [] }: Props) {
  const rows: { name: string; key: string; get: (p: Profile) => number }[] = regions.map((r) => ({
    name: r,
    key: r,
    get: (p) => p[mode][r] ?? 0,
  }))
  if (mode === 'share') {
    rows.push({ name: 'Unassigned (outside atlas regions)', key: '__unassigned', get: (p) => p.unassigned })
  }
  const max = Math.max(1e-9, ...rows.flatMap((r) => profiles.map(r.get)))
  return (
    <section className="profile-chart" aria-label="Network profile">
      <p className="chart-note">Compares where each condition&apos;s evidence lies, not how strong it is.</p>
      <ul className="chart-legend">
        {profiles.map((p, i) => (
          <li key={p.map_id}>
            <span className="swatch" style={{ background: mapColour(i) }} /> {labels[p.map_id] ?? p.map_id}
            {' — '}
            <span className="legend-quantity">{quantityLabel(p, maps.find((m) => m.id === p.map_id))}</span>
          </li>
        ))}
      </ul>
      {rows.map((row) => (
        <div className="chart-row" key={row.key}>
          <div className="chart-region">{row.name}</div>
          <div className="chart-bars">
            {profiles.map((p, i) => {
              const v = row.get(p)
              return (
                <div className="bar-track" key={p.map_id}>
                  <div
                    data-testid="profile-bar"
                    className="bar"
                    style={{ width: `${(v / max) * 100}%`, background: mapColour(i) }}
                    title={`${labels[p.map_id] ?? p.map_id}: ${v.toFixed(3)}`}
                  />
                  <span className="bar-value">
                    {mode === 'share' ? `${(v * 100).toFixed(1)}%` : v.toFixed(2)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </section>
  )
}
