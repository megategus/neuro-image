import type { AtlasFile, MapMeta } from '../data/types'

export const REPO_URL = 'https://github.com/megategus/neuro-image'
export const GPL_URL = 'https://www.gnu.org/licenses/gpl-3.0.html'

interface Props {
  maps: MapMeta[]
  atlas: AtlasFile
  dataBase?: string
}

// Data sources and licences of every shipped (or used) third-party file, from maps.json and atlas.json.
export default function SiteFooter({ maps, atlas, dataBase = `${import.meta.env.BASE_URL}data/` }: Props) {
  const groups = new Map<string, { labels: string[]; map: MapMeta }>()
  for (const m of maps) {
    const key = `${m.citation}|${m.doi}|${m.licence}`
    const g = groups.get(key)
    if (g) g.labels.push(m.label)
    else groups.set(key, { labels: [m.label], map: m })
  }
  return (
    <footer className="site-footer" aria-label="Data sources and licences">
      <h2>Data sources and licences</h2>
      <ul>
        {[...groups.values()].map(({ labels, map }) => (
          <li key={map.id}>
            <strong>{labels.join(', ')}</strong>: {map.citation}{' '}
            <a href={`https://doi.org/${map.doi}`} target="_blank" rel="noreferrer">doi:{map.doi}</a>. Licence: {map.licence}.
          </li>
        ))}
        <li>
          <strong>Background template</strong>: {atlas.template.name}. Licence: {atlas.template.licence}.
        </li>
        {atlas.sources.map((s) => (
          <li key={s.name}>
            <strong>{s.name}</strong>: {s.citation}. Licence: {s.licence}.{' '}
            {s.bundled
              ? 'Shipped as derived region labels.'
              : 'Used to compute network profiles only; not distributed.'}
          </li>
        ))}
      </ul>
      <p>
        Full copyright and licence notices: <a href={`${dataBase}NOTICES.txt`}>NOTICES.txt</a>. This site and
        its data files are distributed under the{' '}
        <a href={GPL_URL} target="_blank" rel="noreferrer">GNU General Public License v3.0</a>; source code:{' '}
        <a href={REPO_URL} target="_blank" rel="noreferrer">{REPO_URL.replace('https://', '')}</a>.
      </p>
    </footer>
  )
}
