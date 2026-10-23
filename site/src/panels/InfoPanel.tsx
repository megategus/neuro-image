import type { MapMeta } from '../data/types'

export default function InfoPanel({ map }: { map: MapMeta }) {
  const rows: [string, React.ReactNode][] = [
    ['Group', map.group],
    ['Study', map.study_id],
    ['Source', map.citation],
    ['DOI', <a key="doi" href={`https://doi.org/${map.doi}`} target="_blank" rel="noreferrer">{map.doi}</a>],
    ['Studies pooled', String(map.n_studies)],
    ['Method', map.method],
    ['Values mean', map.value_meaning],
    ['Threshold', map.threshold_label],
    ['Threshold type', map.threshold_type],
    ['Threshold value', map.threshold === null ? 'none' : String(map.threshold)],
    ['Display range', `${map.display_min} to ${map.display_max}`],
    ['Decreases present', map.has_negative ? 'yes' : 'no'],
    ['Licence', map.licence],
    ['Caveat', map.caveat],
  ]
  return (
    <section className="info-panel" aria-label={`About ${map.label}`}>
      <h3>{map.label}</h3>
      <dl>
        {rows.map(([k, v]) => (
          <div className="info-row" key={k}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      {map.study_id === 'wager2015' && (
        <p className="info-note">No decreases can appear in this map by method</p>
      )}
    </section>
  )
}
