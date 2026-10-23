from dataclasses import replace
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from atlas_pipeline.prepare import background_template, prepare, target_grid
from atlas_pipeline.sources import load_sources

from conftest import MNI_2MM, SOURCES_YAML, make_img

SHAPE = (91, 109, 91)
CACHE = Path(__file__).resolve().parent.parent / ".cache"


def _source(**kw):
    base = load_sources(SOURCES_YAML)[0]
    return replace(base, **kw)


def _vox(affine, xyz):
    return np.round(np.linalg.inv(affine) @ np.array([*xyz, 1.0]))[:3].astype(int)


def _img2mm(fill):
    d = np.zeros(SHAPE, dtype=np.float32)
    fill(d)
    return make_img(SHAPE, MNI_2MM, d)


def test_target_grid():
    t = target_grid()
    assert t.shape == SHAPE
    assert np.array_equal(t.affine, np.array(MNI_2MM, dtype=float))
    assert t.get_fdata().dtype == np.float32 or t.get_data_dtype() == np.float32
    assert not t.get_fdata().any()


def test_background_template():
    t = target_grid()
    bg = background_template(t)
    assert bg.shape == t.shape
    assert np.allclose(bg.affine, t.affine)
    assert bg.get_data_dtype() == np.float32
    assert np.abs(bg.get_fdata()).max() > 0


def test_resamples_3mm_onto_2mm_grid():
    target = target_grid()
    aff3 = np.array([[-3, 0, 0, 90], [0, 3, 0, -126], [0, 0, 3, -72], [0, 0, 0, 1]], float)
    shape3 = (61, 73, 61)
    centre = (22, -4, -12)
    ijk = np.indices(shape3).reshape(3, -1).T
    xyz = nib.affines.apply_affine(aff3, ijk)
    d = np.exp(-((xyz - np.array(centre)) ** 2).sum(1) / (2 * 6.0**2)).reshape(shape3)
    out = prepare(_source(threshold_type="none", threshold=None), make_img(shape3, aff3, d), target).positive
    assert out.shape == SHAPE
    assert np.allclose(out.affine, target.affine)
    peak = np.unravel_index(np.argmax(out.get_fdata()), SHAPE)
    peak_xyz = nib.affines.apply_affine(target.affine, peak)
    assert np.linalg.norm(peak_xyz - np.array(centre)) <= 4


def test_statistical_threshold_zeroes_subthreshold():
    def fill(d):
        d[10, 10, 10] = 2.0
        d[20, 20, 20] = 4.0
        d[30, 30, 30] = -2.0
        d[40, 40, 40] = -4.0

    p = prepare(_source(threshold_type="statistical", threshold=3.1), _img2mm(fill), target_grid())
    pos = p.positive.get_fdata()
    assert pos[10, 10, 10] == 0 and pos[20, 20, 20] == 4.0
    neg = p.negative.get_fdata()
    assert neg[30, 30, 30] == 0 and neg[40, 40, 40] == 4.0
    assert p.display_min == 3.1


def test_display_only_keeps_all_values():
    p = prepare(
        _source(threshold_type="display-only", threshold=0.001),
        _img2mm(lambda d: d.__setitem__((5, 5, 5), 0.0005)),
        target_grid(),
    )
    assert p.positive.get_fdata()[5, 5, 5] == pytest.approx(0.0005)
    assert p.display_min == 0.001


def test_sign_split():
    def fill(d):
        d[1, 1, 1] = -2
        d[2, 2, 2] = 3

    p = prepare(_source(threshold_type="none", threshold=None), _img2mm(fill), target_grid())
    assert p.positive.get_fdata().max() == 3
    assert p.negative.get_fdata().max() == 2
    assert p.positive.get_fdata().min() >= 0
    assert p.display_min == 0
    assert p.display_max == pytest.approx(3.0, rel=1e-3)
    for im in (p.positive, p.negative):
        assert im.get_data_dtype() == np.float32


def test_no_negatives_gives_none():
    p = prepare(
        _source(threshold_type="none", threshold=None),
        _img2mm(lambda d: d.__setitem__((2, 2, 2), 1.0)),
        target_grid(),
    )
    assert p.negative is None


def test_same_grid_skips_resampling():
    d = np.zeros(SHAPE, dtype=np.float32)
    d[3, 3, 3] = 1.0
    d[4, 3, 3] = 0.5
    p = prepare(_source(threshold_type="none", threshold=None), make_img(SHAPE, MNI_2MM, d), target_grid())
    assert np.array_equal(p.positive.get_fdata(), d)


@pytest.mark.skipif(
    not (CACHE / "Wager_Kang_PlosCB_emometa_2015_fear.nii.gz").exists(), reason="cached Wager map absent"
)
def test_real_wager_fear_map():
    src = next(s for s in load_sources(SOURCES_YAML) if s.id == "fear")
    img = nib.load(CACHE / "Wager_Kang_PlosCB_emometa_2015_fear.nii.gz")
    p = prepare(src, img, target_grid())
    assert p.positive.shape == SHAPE
    assert p.negative is None
    assert p.display_min == 0.001
