import json
from dataclasses import replace
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from atlas_pipeline import build as build_mod
from atlas_pipeline.atlas import LABELS, ReferenceAtlas
from atlas_pipeline.build import run_build
from atlas_pipeline.prepare import TARGET_AFFINE, TARGET_SHAPE, target_grid
from atlas_pipeline.sources import Source

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DOC = {"reviewed": False, "lessons": [
    {"id": "a", "title": "T", "map_ids": ["fear", "anxiety"], "view": "both",
     "body": ["TODO-draft"], "notice": "TODO-draft", "claims": []}]}


@pytest.fixture
def LESSONS(tmp_path):
    p = tmp_path / "lessons.json"
    p.write_text(json.dumps(LESSONS_DOC))
    return p

SRC = Source(
    id="fear", label="Fear", group="emotion", study_id="w", url="http://x/fear.nii.gz",
    sha256=None, status="verified", citation="c", doi="10.1/x", n_studies=5, method="m",
    value_meaning="v", threshold=0.001, threshold_type="display-only", licence="l",
    caveat="TODO-caveat",
)
UNVERIFIED = replace(SRC, id="anxiety", label="Anxiety", group="anxiety", status="unverified",
                     url="http://x/", threshold=None, threshold_type="none")


def fake_fetch(source, cache_dir):
    rng = np.random.default_rng(0)
    data = np.zeros(TARGET_SHAPE, dtype=np.float32)
    data[30:60, 40:70, 30:60] = rng.random((30, 30, 30)).astype(np.float32) + 0.1
    path = Path(cache_dir) / f"{source.id}.nii.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, TARGET_AFFINE), path)
    return path


def fake_atlas(target, cache_dir, bundled=(True, False)):
    lab = np.zeros(TARGET_SHAPE, dtype=np.int16)
    lab[20:50, 40:100, 20:70] = 1       # Yeo-like
    lab[50:70, 40:100, 20:70] = 8       # HO-like
    return ReferenceAtlas(
        img=nib.Nifti1Image(lab, target.affine),
        labels=dict(LABELS),
        sources=[
            {"name": "Y", "citation": "yc", "licence": "MIT", "bundled": bundled[0]},
            {"name": "H", "citation": "hc", "licence": "FSL", "bundled": bundled[1]},
        ],
    )


def go(tmp_path, lessons, sources, deploy=False, atlas_fn=fake_atlas, fetch_fn=fake_fetch):
    out = tmp_path / "out"
    problems = run_build(sources, lessons, out, tmp_path / "cache", deploy=deploy,
                         fetch_fn=fetch_fn, atlas_fn=atlas_fn)
    return problems, out


def test_unverified_source_listed_unavailable(tmp_path, LESSONS):
    problems, out = go(tmp_path, LESSONS, [SRC, UNVERIFIED])
    assert problems == []
    maps = json.loads((out / "maps.json").read_text())
    assert maps["unavailable"][0]["id"] == "anxiety"
    assert maps["unavailable"][0]["reason"] == "source not yet verified"
    assert [m["id"] for m in maps["maps"]] == ["fear"]


def test_outputs(tmp_path, LESSONS):
    problems, out = go(tmp_path, LESSONS, [SRC, UNVERIFIED])
    assert problems == []
    m = json.loads((out / "maps.json").read_text())["maps"][0]
    assert m["threshold_label"] == "display threshold chosen by the authors — not a significance test"
    assert m["files"] == {"pos": "maps/fear_pos.nii.gz", "neg": None}
    assert m["has_negative"] is False
    pos = nib.load(out / "maps" / "fear_pos.nii.gz")
    assert pos.get_data_dtype() == np.float32 and tuple(pos.shape) == TARGET_SHAPE
    tpl = nib.load(out / "template.nii.gz")
    assert tpl.get_data_dtype() == np.float32
    prof = json.loads((out / "profiles.json").read_text())
    assert prof["regions"] == [LABELS[i] for i in range(1, 12)]
    assert prof["profiles"][0]["map_id"] == "fear"
    atlas = json.loads((out / "atlas.json").read_text())
    assert atlas["labels"]["8"] == {"name": "Amygdala", "displayable": False}
    assert atlas["labels"]["1"]["displayable"] is True
    assert atlas["template"]["licence"].startswith("MNI template licence")
    assert (out / "lessons.json").exists()


def test_atlas_file_has_only_bundled_labels(tmp_path, LESSONS):
    problems, out = go(tmp_path, LESSONS, [SRC, UNVERIFIED])
    assert problems == []
    img = nib.load(out / "atlas_labels.nii.gz")
    data = np.asarray(img.dataobj)
    assert img.get_data_dtype() == np.uint8
    assert set(np.unique(data)) == {0, 1}


def test_atlas_file_not_written_when_nothing_bundled(tmp_path, LESSONS):
    problems, out = go(tmp_path, LESSONS, [SRC, UNVERIFIED], atlas_fn=lambda t, c: fake_atlas(t, c, (False, False)))
    assert problems == []
    assert not (out / "atlas_labels.nii.gz").exists()


def test_deploy_fails_on_todo_caveat_and_unreviewed(tmp_path, LESSONS):
    problems, _ = go(tmp_path, LESSONS, [SRC, UNVERIFIED], deploy=True)
    text = "\n".join(problems)
    assert "caveat" in text and "reviewed" in text


def test_failed_verification_is_build_error(tmp_path, LESSONS):
    def bad_fetch(source, cache_dir):
        p = Path(cache_dir) / "bad.nii.gz"
        p.parent.mkdir(parents=True, exist_ok=True)
        nib.save(nib.Nifti1Image(np.zeros((4, 4, 4), np.float32), np.eye(4)), p)
        return p

    problems, _ = go(tmp_path, LESSONS, [SRC, UNVERIFIED], fetch_fn=bad_fetch)
    assert any("fear" in p and "no non-zero" in p for p in problems)


def test_cli_exit_code(tmp_path, monkeypatch, LESSONS):
    from atlas_pipeline.__main__ import main

    monkeypatch.setattr(build_mod, "default_fetch", fake_fetch)
    monkeypatch.setattr(build_mod, "default_atlas", fake_atlas)
    monkeypatch.setattr(build_mod, "load_sources", lambda p: [SRC, UNVERIFIED])
    assert main(["build", "--out", str(tmp_path / "o"), "--cache", str(tmp_path / "c"), "--lessons", str(LESSONS)]) == 0
    assert main(["build", "--deploy", "--out", str(tmp_path / "o"), "--cache", str(tmp_path / "c"), "--lessons", str(LESSONS)]) == 1
