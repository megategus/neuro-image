export const UNTHRESHOLDED_LABEL = 'unthresholded — all values shown'

// What the line under the slider says: it must describe the cut actually in use.
export function cutLabel(authorsLabel: string, authorsCut: number, cut: number | null, unthresholded: boolean): string {
  if (unthresholded) return UNTHRESHOLDED_LABEL
  if (cut === null || cut === authorsCut) return authorsLabel
  return `display cut set by you: ${cut} — not a significance test (authors' display threshold: ${authorsCut})`
}
