// Okabe-Ito colour-blind-safe palette.
export const PALETTE = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#000000']
export const mapColour = (i: number) => PALETTE[i % PALETTE.length]
