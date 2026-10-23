"""Put source maps on the common MNI152 2 mm grid and split them by sign."""
from __future__ import annotations

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


def prepare(source: Source, img: nib.Nifti1Image, target: nib.Nifti1Image) -> PreparedMap:
    if not _same_grid(img, target):
        img = _resample(img, target)
    data = np.nan_to_num(np.asarray(img.get_fdata(), dtype=np.float32))

    if source.threshold_type == "statistical" and source.threshold is not None:
        data = np.where(np.abs(data) < source.threshold, 0.0, data)

    pos = np.where(data > 0, data, 0.0)
    neg = np.where(data < 0, -data, 0.0)

    display_min = float(source.threshold or 0)
    nonzero = pos[pos > 0]
    display_max = float(np.percentile(nonzero, 99.9)) if nonzero.size else display_min

    return PreparedMap(
        source=source,
        positive=_as_img(pos, target),
        negative=_as_img(neg, target) if neg.any() else None,
        display_min=display_min,
        display_max=display_max,
    )
