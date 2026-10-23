import dataclasses

import nibabel as nib
import numpy as np
import pytest

from atlas_pipeline.atlas import ReferenceAtlas
from atlas_pipeline.prepare import PreparedMap
from atlas_pipeline.profile import compute_profile
from atlas_pipeline.sources import Source
from conftest import MNI_2MM

SHAPE = (4, 4, 4)


def _atlas(full=False):
    lab = np.zeros(SHAPE, dtype=np.float32)
    lab[0, :, :] = 1  # 16 voxels
    lab[1, :, :] = 2  # 16 voxels
    lab[2, :2, :] = 3  # 8 voxels
    # remaining 24 voxels unlabelled (or label 3 as well when full: 32 voxels)
    if full:
        lab[2:, :, :] = 3
    img = nib.Nifti1Image(lab, np.array(MNI_2MM, dtype=float))
    return ReferenceAtlas(img=img, labels={1: "A", 2: "B", 3: "C"}, sources=[])


def _pm(data, threshold_type):
    base = Source(
        id="x", label="x", group="emotion", study_id="s", url="u", sha256=None,
        status="verified", citation="c", doi="d", n_studies=None, method="m",
        value_meaning="v", threshold=None, threshold_type=threshold_type, licence="l", caveat="",
    )
    img = nib.Nifti1Image(np.asarray(data, dtype=np.float32), np.array(MNI_2MM, dtype=float))
    return PreparedMap(source=base, positive=img, negative=None, display_min=0.0, display_max=1.0)


def test_shares_plus_unassigned_sum_to_one():
    rng = np.random.default_rng(0)
    p = compute_profile(_pm(rng.random(SHAPE), "display-only"), _atlas())
    assert sum(p.share.values()) + p.unassigned == pytest.approx(1.0, abs=1e-6)


def test_statistical_map_uses_voxel_share():
    data = np.zeros(SHAPE)
    data[0, 0, 0] = 100.0  # one huge voxel in A
    data[1, 0, 0] = 1.0
    data[1, 0, 1] = 1.0
    data[1, 0, 2] = 1.0
    p = compute_profile(_pm(data, "statistical"), _atlas())
    assert p.quantity == "voxel_share"
    assert p.share["A"] == pytest.approx(0.25)
    assert p.share["B"] == pytest.approx(0.75)


def test_display_only_map_uses_intensity_share():
    data = np.zeros(SHAPE)
    data[0, 0, 0] = 3.0
    data[1, 0, 0] = 1.0
    p = compute_profile(_pm(data, "display-only"), _atlas())
    assert p.quantity == "intensity_share"
    assert p.share["A"] == pytest.approx(0.75)
    assert p.share["B"] == pytest.approx(0.25)
    assert p.map_id == "x"


def test_size_normalised_equal_density_is_one():
    # Fully labelled atlas: share is a fraction of the in-brain total, so equal
    # density gives 1.0 only when no signal falls outside the labels.
    p = compute_profile(_pm(np.ones(SHAPE), "display-only"), _atlas(full=True))
    for name in ("A", "B", "C"):
        assert p.size_normalised[name] == pytest.approx(1.0)


def test_unassigned_share():
    p = compute_profile(_pm(np.ones(SHAPE), "statistical"), _atlas())
    assert p.unassigned == pytest.approx(24 / 64)


def test_zero_voxel_region_is_omitted():
    atlas = _atlas()
    atlas = dataclasses.replace(atlas, labels={**atlas.labels, 4: "Empty"})
    p = compute_profile(_pm(np.ones(SHAPE), "display-only"), atlas)
    assert "Empty" not in p.size_normalised
    assert p.share["Empty"] == 0.0


def test_empty_map_raises():
    with pytest.raises(ValueError):
        compute_profile(_pm(np.zeros(SHAPE), "display-only"), _atlas())
