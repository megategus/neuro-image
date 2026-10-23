import json

import numpy as np

from atlas_pipeline.verify import verify

from conftest import MNI_2MM, make_img

SHAPE = (91, 109, 91)


def _positive(seed=0):
    rng = np.random.default_rng(seed)
    return rng.uniform(0.5, 5.0, SHAPE)


def test_wager_like_map_ok():
    r = verify(make_img(SHAPE, MNI_2MM, _positive()))
    assert r.ok and r.is_mni and r.has_negative is False
    assert r.is_thresholded is False
    assert r.shape == SHAPE and r.zooms == (2.0, 2.0, 2.0)


def test_detects_negative_values():
    d = _positive()
    d[0, 0, 0] = -1.5
    r = verify(make_img(SHAPE, MNI_2MM, d))
    assert r.has_negative is True


def test_rejects_4d():
    img = make_img((10, 10, 10, 2), np.eye(4), np.ones((10, 10, 10, 2)))
    r = verify(img)
    assert r.ok is False
    assert any("4D" in p for p in r.problems)


def test_rejects_non_mni_affine():
    r = verify(make_img(SHAPE, np.eye(4), _positive()))
    assert r.is_mni is False
    assert r.ok is False


def test_flags_prethresholded():
    d = _positive().ravel()
    d[: int(0.6 * d.size)] = 0
    d[int(0.6 * d.size)] = 3.1
    d[d > 0] = np.maximum(d[d > 0], 3.1)
    r = verify(make_img(SHAPE, MNI_2MM, d))
    assert r.is_thresholded is True
    assert np.isclose(r.min, 3.1, atol=1e-6)


def test_nan_reported_but_ok():
    d = _positive()
    d[0, 0, 0] = np.nan
    r = verify(make_img(SHAPE, MNI_2MM, d))
    assert r.ok
    assert "contains NaN" in r.problems


def test_report_is_json_serialisable():
    from dataclasses import asdict

    json.dumps(asdict(verify(make_img(SHAPE, MNI_2MM, _positive()))))
