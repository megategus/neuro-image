import { cmapper } from '@niivue/niivue'

// CSS gradient built from the control points of NiiVue's own colour map, so
// the colour bar shows exactly the colours NiiVue draws (cal_min -> cal_max).
// NiiVue also ramps opacity along the map; the bar shows the opaque colours.
export function colormapGradient(name: string): string {
  const cm = cmapper.colormapFromKey(name)
  const last = cm.I[cm.I.length - 1] || 255
  const stops = cm.I.map((pos, k) => {
    const pct = Math.round((pos / last) * 1000) / 10
    return `rgb(${cm.R[k]}, ${cm.G[k]}, ${cm.B[k]}) ${pct}%`
  })
  return `linear-gradient(90deg, ${stops.join(', ')})`
}
