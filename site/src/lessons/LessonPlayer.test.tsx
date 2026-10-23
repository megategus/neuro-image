import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import LessonPlayer from './LessonPlayer'
import type { Lesson, LessonsFile } from '../data/types'

const lesson = (over: Partial<Lesson>): Lesson => ({
  id: 'l', title: 'T', map_ids: ['fear'], view: 'overlay', body: ['p'], notice: 'n', claims: [], ...over,
})
const file = (reviewed: boolean): LessonsFile => ({
  reviewed,
  lessons: [
    lesson({ id: 'a', title: 'First lesson', body: ['Para <b>one</b>', 'Para two'], notice: 'Mind this',
      claims: [{ text: 'A claim', source_doi: '10.1/abc' }] }),
    lesson({ id: 'b', title: 'Second lesson', map_ids: ['anger', 'fear'], view: 'both' }),
    lesson({ id: 'c', title: 'Third lesson', map_ids: ['anxiety'] }),
  ],
})

describe('LessonPlayer', () => {
  it('renders lesson 1, progress, body as text, notice and claims', () => {
    render(<LessonPlayer lessons={file(true)} onLoadMaps={vi.fn()} onExit={vi.fn()} />)
    expect(screen.getByRole('heading', { name: 'First lesson' })).toBeInTheDocument()
    expect(screen.getByText('Lesson 1 of 3')).toBeInTheDocument()
    expect(screen.getByText('Para <b>one</b>')).toBeInTheDocument()
    expect(screen.getByText('Mind this')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /10\.1\/abc/ })).toHaveAttribute('href', 'https://doi.org/10.1/abc')
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
  })

  it('Next moves on and loads that lesson maps', () => {
    const onLoadMaps = vi.fn()
    render(<LessonPlayer lessons={file(true)} onLoadMaps={onLoadMaps} onExit={vi.fn()} />)
    expect(onLoadMaps).toHaveBeenCalledWith(['fear'], 'overlay')
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByRole('heading', { name: 'Second lesson' })).toBeInTheDocument()
    expect(onLoadMaps).toHaveBeenLastCalledWith(['anger', 'fear'], 'both')
  })

  it('draft banner only while unreviewed', () => {
    const { unmount } = render(<LessonPlayer lessons={file(false)} onLoadMaps={vi.fn()} onExit={vi.fn()} />)
    expect(screen.getByText('Draft — not yet medically reviewed')).toBeInTheDocument()
    unmount()
    render(<LessonPlayer lessons={file(true)} onLoadMaps={vi.fn()} onExit={vi.fn()} />)
    expect(screen.queryByText('Draft — not yet medically reviewed')).toBeNull()
  })

  it('unavailable lesson shows message, skips onLoadMaps, stays navigable; last disables Next', () => {
    const onLoadMaps = vi.fn()
    render(<LessonPlayer lessons={file(true)} unavailableIds={['anxiety']} initialIndex={2}
      onLoadMaps={onLoadMaps} onExit={vi.fn()} />)
    expect(screen.getByText('This lesson needs data not yet available')).toBeInTheDocument()
    expect(onLoadMaps).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Previous' }))
    expect(screen.getByRole('heading', { name: 'Second lesson' })).toBeInTheDocument()
  })

  it('Explore freely calls onExit; index changes are reported', () => {
    const onExit = vi.fn()
    const onIndexChange = vi.fn()
    render(<LessonPlayer lessons={file(true)} onLoadMaps={vi.fn()} onExit={onExit} onIndexChange={onIndexChange} />)
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(onIndexChange).toHaveBeenLastCalledWith(1)
    fireEvent.click(screen.getByRole('button', { name: 'Explore freely' }))
    expect(onExit).toHaveBeenCalled()
  })

  it('calls onUnavailable (not onLoadMaps) when an unavailable lesson becomes current', () => {
    const onUnavailable = vi.fn()
    const onLoadMaps = vi.fn()
    render(<LessonPlayer lessons={file(true)} unavailableIds={['anxiety']} initialIndex={1}
      onLoadMaps={onLoadMaps} onUnavailable={onUnavailable} onExit={vi.fn()} />)
    expect(onUnavailable).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(onUnavailable).toHaveBeenCalledTimes(1)
    expect(onLoadMaps).toHaveBeenCalledTimes(1)
  })
})
