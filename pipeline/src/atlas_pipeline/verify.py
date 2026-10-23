"""Sanity checks for candidate meta-analytic maps before they enter the atlas."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import nibabel as nib
import numpy as np

# FSL MNI152 field of view (mm), expanded by _MARGIN when checking corners.
_MNI_X = (-91.0, 91.0)
_MNI_Y = (-126.0, 91.0)
_MNI_Z = (-72.0, 109.0)
_MARGIN = 3.0
_THRESHOLDED_ZERO_FRACTION = 0.30


@dataclass
class VerificationReport:
    ok: bool
    shape: tuple[int, ...]
    zooms: tuple[float, ...]
    is_mni: bool
    has_negative: bool
    is_thresholded: bool
    min: float
    max: float
    problems: list[str] = field(default_factory=list)


def _is_mni(img: nib.Nifti1Image) -> bool:
    """MNI152-space check.

    True when (1) the axis codes from ``nib.aff2axcodes`` are ('R','A','S') or
    ('L','A','S'), and (2) the world coordinates of all eight corner voxels
    lie within the MNI152 bounds (x [-91,91], y [-126,91], z [-72,109] mm)
    expanded by 3 mm.
    """
    if tuple(nib.aff2axcodes(img.affine)) not in {("R", "A", "S"), ("L", "A", "S")}:
        return False
    last = np.array(img.shape[:3]) - 1
    corners = np.array(list(product(*[(0, n) for n in last])), dtype=float)
    world = nib.affines.apply_affine(img.affine, corners)
    for axis, (lo, hi) in enumerate((_MNI_X, _MNI_Y, _MNI_Z)):
        if world[:, axis].min() < lo - _MARGIN or world[:, axis].max() > hi + _MARGIN:
            return False
    return True


def _mask_on_grid(mask: nib.Nifti1Image, img: nib.Nifti1Image) -> np.ndarray:
    if mask.shape[:3] != img.shape[:3] or not np.allclose(mask.affine, img.affine):
        from nilearn.image import resample_to_img

        mask = resample_to_img(mask, img, interpolation="nearest")
    return np.asarray(mask.dataobj) > 0


def verify(img: nib.Nifti1Image, brain_mask: nib.Nifti1Image | None = None) -> VerificationReport:
    """Check shape, space, sign and thresholding of a candidate map.

    In-brain voxels are those with ``brain_mask > 0`` (the mask is resampled
    to the image grid with nearest neighbour unless shape and affine already
    match); without a mask they are all finite voxels. The thresholded
    heuristic: more than 30% of in-brain voxels exactly zero. ``min``/``max``
    are over the absolute values of non-zero finite voxels. NaNs are
    reported but do not fail.
    """
    shape = tuple(int(n) for n in img.shape)
    zooms = tuple(float(z) for z in img.header.get_zooms()[: len(shape)])
    problems: list[str] = []
    if len(shape) != 3:
        problems.append("4D image: choose a volume")
        return VerificationReport(False, shape, zooms, False, False, False, float("nan"), float("nan"), problems)

    data = np.asarray(img.dataobj, dtype=np.float64)
    finite = np.isfinite(data)
    if not finite.all():
        problems.append("contains NaN")
    vals = data[finite]
    nonzero = vals[vals != 0]
    is_mni = _is_mni(img)
    if not is_mni:
        problems.append("not in MNI152 space (axes must be RAS/LAS and corners within MNI bounds +3 mm)")
    if nonzero.size == 0:
        problems.append("no non-zero values")
        vmin = vmax = float("nan")
        thresholded = False
    else:
        absnz = np.abs(nonzero)
        vmin, vmax = float(absnz.min()), float(absnz.max())
        inbrain = finite if brain_mask is None else finite & _mask_on_grid(brain_mask, img)
        n_in = int(inbrain.sum())
        zero_frac = float((data[inbrain] == 0).mean()) if n_in else 0.0
        thresholded = zero_frac > _THRESHOLDED_ZERO_FRACTION
    has_negative = bool((nonzero < 0).any())
    ok = is_mni and nonzero.size > 0
    return VerificationReport(ok, shape, zooms, is_mni, has_negative, thresholded, vmin, vmax, problems)
