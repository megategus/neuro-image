"""Put source maps on the common MNI152 2 mm grid and split them by sign."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import nibabel as nib
import numpy as np
from nilearn.datasets import load_mni152_template
from nilearn.image import resample_to_img

from .sources import Source

TARGET_SHAPE = (91, 109, 91)
TARGET_AFFINE = np.array(
    [[-2, 0, 0, 90], [0, 2, 0, -126], [0, 0, 2, -72], [0, 0, 0, 1]], dtype=float
)


@dataclass
class PreparedMap:
    source: Source
    positive: nib.Nifti1Image
    negative: nib.Nifti1Image | None
    display_min: float
    display_max: float


def target_grid() -> nib.Nifti1Image:
    """All-zero float32 image on the FSL MNI152 2 mm grid used by the source maps."""
    return nib.Nifti1Image(np.zeros(TARGET_SHAPE, dtype=np.float32), TARGET_AFFINE.copy())


def _same_grid(a: nib.Nifti1Image, b: nib.Nifti1Image) -> bool:
    return tuple(a.shape) == tuple(b.shape) and np.allclose(a.affine, b.affine, atol=1e-4)


def _resample(img: nib.Nifti1Image, target: nib.Nifti1Image) -> nib.Nifti1Image:
    # force_resample/copy_header opt in to nilearn's future defaults, which avoids
    # its FutureWarning without hiding warnings globally.
    # A sign part that happens to hold only 0/1 trips nilearn's binary-image
    # warning; continuous interpolation is the deliberate choice here, so that one
    # message is silenced locally (not globally).
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Resampling binary images")
        return resample_to_img(
            img, target, interpolation="continuous", force_resample=True, copy_header=True
        )


def background_template(target: nib.Nifti1Image) -> nib.Nifti1Image:
    """nilearn's bundled MNI152 template resampled onto `target` (float32)."""
    out = _resample(load_mni152_template(resolution=2), target)
    return nib.Nifti1Image(np.asarray(out.get_fdata(), dtype=np.float32), target.affine)


def _as_img(data: np.ndarray, target: nib.Nifti1Image) -> nib.Nifti1Image:
    img = nib.Nifti1Image(np.ascontiguousarray(data, dtype=np.float32), target.affine)
    img.set_data_dtype(np.float32)
    return img


def _part(data: np.ndarray, like: nib.Nifti1Image, target: nib.Nifti1Image, regrid: bool) -> np.ndarray:
    """One sign part (non-negative) on the target grid; clipped to remove spline ringing."""
    if not regrid:
        return data
    out = _resample(nib.Nifti1Image(data, like.affine), target)
    return np.clip(np.asarray(out.get_fdata(), dtype=np.float32), 0.0, None)


def prepare(source: Source, img: nib.Nifti1Image, target: nib.Nifti1Image) -> PreparedMap:
    regrid = not _same_grid(img, target)
    raw = np.asarray(img.get_fdata(), dtype=np.float32)
    raw = np.where(np.isfinite(raw), raw, 0.0).astype(np.float32)

    # Split by sign on the source grid, then resample each part: resampling a
    # signed or positive-only map directly would create spurious negatives.
    pos = _part(np.where(raw > 0, raw, 0.0).astype(np.float32), img, target, regrid)
    has_neg = bool((raw < 0).any())
    neg = _part(np.where(raw < 0, -raw, 0.0).astype(np.float32), img, target, regrid) if has_neg else None

    threshold = source.threshold if source.threshold is not None else 0.0
    if source.threshold_type == "statistical":
        pos = np.where(pos < threshold, 0.0, pos)
        if neg is not None:
            neg = np.where(neg < threshold, 0.0, neg)

    display_min = float(threshold)
    nonzero = pos[pos > 0]
    display_max = float(np.percentile(nonzero, 99.9)) if nonzero.size else display_min

    return PreparedMap(
        source=source,
        positive=_as_img(pos, target),
        negative=_as_img(neg, target) if neg is not None and neg.any() else None,
        display_min=display_min,
        display_max=display_max,
    )
