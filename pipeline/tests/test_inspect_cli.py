import json

import nibabel as nib
import numpy as np

from atlas_pipeline import inspect_cli
from atlas_pipeline.__main__ import main

from conftest import MNI_2MM, make_img


def _no_mask(monkeypatch):
    monkeypatch.setattr(inspect_cli, "_load_mask", lambda: None)


def test_missing_file_is_one_line_error(tmp_path, monkeypatch, capsys):
    _no_mask(monkeypatch)
    assert main(["inspect", str(tmp_path / "nope.nii.gz")]) == 1
    err = capsys.readouterr().err.strip()
    assert err.startswith("error:") and "\n" not in err


def test_corrupt_cached_mask_deleted_and_warned(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(inspect_cli, "CACHE_DIR", tmp_path)
    bad = tmp_path / "tpl-MNI152NLin6Asym_res-02_desc-brain_mask.nii.gz"
    bad.write_bytes(b"not a nifti")
    assert inspect_cli._load_mask() is None
    assert not bad.exists()
    assert "warning" in capsys.readouterr().err


def test_all_zero_map_emits_null_not_nan(tmp_path, monkeypatch, capsys):
    _no_mask(monkeypatch)
    p = tmp_path / "z.nii.gz"
    nib.save(make_img((91, 109, 91), MNI_2MM, np.zeros(91 * 109 * 91)), p)
    assert main(["inspect", str(p)]) == 0
    out = capsys.readouterr().out
    assert "NaN" not in out
    d = json.loads(out)
    assert d["min"] is None and d["max"] is None
