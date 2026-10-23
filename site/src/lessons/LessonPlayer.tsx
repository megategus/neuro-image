import { useEffect, useRef, useState } from 'react'
import type { LessonsFile } from '../data/types'

export type LessonView = 'overlay' | 'profile' | 'both'

interface Props {
  lessons: LessonsFile
  unavailableIds?: string[]
  initialIndex?: number
  onLoadMaps: (ids: string[], view: LessonView) => void
  onExit: () => void
  onIndexChange?: (index: number) => void
}

export default function LessonPlayer({
  lessons, unavailableIds = [], initialIndex = 0, onLoadMaps, onExit, onIndexChange,
}: Props) {
  const total = lessons.lessons.length
  const [index, setIndex] = useState(Math.min(Math.max(initialIndex, 0), Math.max(total - 1, 0)))
  const lesson = lessons.lessons[index]
  const unavailable = lesson ? lesson.map_ids.some((id) => unavailableIds.includes(id)) : false

  const loadRef = useRef(onLoadMaps)
  const idxRef = useRef(onIndexChange)
  useEffect(() => {
    loadRef.current = onLoadMaps
    idxRef.current = onIndexChange
  })

  useEffect(() => {
    idxRef.current?.(index)
    if (lesson && !unavailable) loadRef.current(lesson.map_ids, lesson.view)
  }, [index, lesson, unavailable])

  if (!lesson) return <p>No lessons available.</p>

  return (
    <article className="lesson-player">
      {!lessons.reviewed && <p className="draft-banner" role="note">Draft — not yet medically reviewed</p>}
      <p className="lesson-progress">Lesson {index + 1} of {total}</p>
      <h2>{lesson.title}</h2>
      {unavailable ? (
        <p className="lesson-unavailable">This lesson needs data not yet available</p>
      ) : (
        <>
          {lesson.body.map((p, i) => <p key={i}>{p}</p>)}
          <aside className="lesson-notice" aria-label="Notice">
            <strong>Notice</strong>
            <p>{lesson.notice}</p>
          </aside>
          {lesson.claims.length > 0 && (
            <ul className="lesson-claims">
              {lesson.claims.map((c, i) => (
                <li key={i}>
                  {c.text}{' '}
                  <a href={`https://doi.org/${c.source_doi}`} target="_blank" rel="noreferrer">
                    doi:{c.source_doi}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <nav className="lesson-nav">
        <button onClick={() => setIndex(index - 1)} disabled={index === 0}>Previous</button>
        <button onClick={() => setIndex(index + 1)} disabled={index >= total - 1}>Next</button>
        <button onClick={onExit}>Explore freely</button>
      </nav>
    </article>
  )
}
