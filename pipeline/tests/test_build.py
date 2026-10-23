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
LESSONS_DOC = {"lessons": [
    {"id": "a", "title": "T", "map_ids": ["fear", "anxiety"], "view": "both", "reviewed": False,
     "body": ["TODO-draft"], "notice": "TODO-draft", "claims": []}]}


def lessons_file(tmp_path, doc):
    p = tmp_path / "lessons.json"
    p.write_text(json.dumps(doc))
    return p


@pytest.fixture
def LESSONS(tmp_path):
    return lessons_file(tmp_path, LESSONS_DOC)


def fear_lesson(reviewed):
    return {"id": "f", "title": "Fear", "map_ids": ["fear"], "view": "overlay", "reviewed": reviewed,
            "body": ["Real text."], "notice": "Look.", "claims": []}

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


def fake_mask(cache_dir, region=(slice(30, 60), slice(40, 70), slice(30, 60))):
    """Brain mask equal to fake_fetch's non-zero block, so that map is not 'thresholded'."""
    m = np.zeros(TARGET_SHAPE, dtype=np.uint8)
    m[region] = 1
    return nib.Nifti1Image(m, TARGET_AFFINE)


def go(tmp_path, lessons, sources, deploy=False, atlas_fn=fake_atlas, fetch_fn=fake_fetch,
       mask_fn=fake_mask):
    out = tmp_path / "out"
    problems = run_build(sources, lessons, out, tmp_path / "cache", deploy=deploy,
                         fetch_fn=fetch_fn, atlas_fn=atlas_fn, mask_fn=mask_fn)
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
    assert atlas["template"]["licence"].startswith("MNI ICBM152 licence")
    assert "Louis Collins" in atlas["template"]["notice"]
    assert m["caveat_reviewed"] is False
    assert json.loads((out / "lessons.json").read_text())["lessons"][0]["reviewed"] is False


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


def test_deploy_blocks_unreviewed_lesson_whose_maps_are_all_available(tmp_path):
    src = replace(SRC, caveat="Real caveat.", caveat_reviewed=True)
    les = lessons_file(tmp_path, {"lessons": [fear_lesson(False)]})
    problems, _ = go(tmp_path, les, [src, UNVERIFIED], deploy=True)
    assert len(problems) == 1 and "'f'" in problems[0] and "not yet medically reviewed" in problems[0]


def test_deploy_ignores_unreviewed_lesson_needing_unverified_map(tmp_path):
    src = replace(SRC, caveat="Real caveat.", caveat_reviewed=True)
    les = lessons_file(tmp_path, {"lessons": [
        fear_lesson(True),
        {**fear_lesson(False), "id": "g", "map_ids": ["fear", "anxiety"]},
    ]})
    problems, _ = go(tmp_path, les, [src, UNVERIFIED], deploy=True)
    assert problems == []


def test_deploy_blocks_unreviewed_caveat_of_verified_source_only(tmp_path):
    les = lessons_file(tmp_path, {"lessons": [fear_lesson(True)]})
    src = replace(SRC, caveat="Real caveat.", caveat_reviewed=False)
    problems, _ = go(tmp_path, les, [src, UNVERIFIED], deploy=True)  # UNVERIFIED is also unreviewed
    assert problems == ["map 'fear': caveat not yet medically reviewed "
                        "(set caveat_reviewed: true in sources.yaml after review)"]
    problems, _ = go(tmp_path, les, [replace(src, caveat_reviewed=True), UNVERIFIED], deploy=True)
    assert problems == []


def test_pre_thresholded_map_without_statistical_threshold_is_build_error(tmp_path, LESSONS):
    big = (slice(10, 80), slice(10, 100), slice(10, 80))  # fake map is zero in most of this mask
    problems, out = go(tmp_path, LESSONS, [SRC, UNVERIFIED], mask_fn=lambda c: fake_mask(c, big))
    assert any("fear" in p and "pre-thresholded" in p for p in problems)
    assert json.loads((out / "maps.json").read_text())["maps"] == []
    none_src = replace(SRC, threshold_type="none", threshold=None)
    problems, _ = go(tmp_path, LESSONS, [none_src, UNVERIFIED], mask_fn=lambda c: fake_mask(c, big))
    assert any("pre-thresholded" in p for p in problems)
    stat = replace(SRC, threshold_type="statistical", threshold=0.05)
    problems, _ = go(tmp_path, LESSONS, [stat, UNVERIFIED], mask_fn=lambda c: fake_mask(c, big))
    assert problems == []


def test_missing_brain_mask_is_build_error(tmp_path, LESSONS):
    def no_mask(cache_dir):
        raise OSError("offline")
    problems, _ = go(tmp_path, LESSONS, [SRC, UNVERIFIED], mask_fn=no_mask)
    assert any(p.startswith("brain mask:") for p in problems)


def test_notices_file_lists_sources_and_licence_texts(tmp_path, LESSONS):
    from atlas_pipeline.atlas import SOURCES
    problems, out = go(tmp_path, LESSONS, [SRC, UNVERIFIED],
                       atlas_fn=lambda t, c: replace(fake_atlas(t, c), sources=[dict(s) for s in SOURCES]))
    assert problems == []
    text = (out / "NOTICES.txt").read_text()
    assert "https://github.com/megategus/neuro-image" in text
    assert "gpl-3.0" in text
    assert "Fear:" in text and "doi:10.1/x" in text and "Licence: l" in text
    assert "Copyright (C) 1993-2004 Louis Collins" in text
    assert "provided that the above copyright notice appear in all copies" in text
    assert "Copyright (c) 2016 Computational Brain Imaging Group (CBIG)" in text
    assert "The above copyright notice and this permission notice shall be included" in text
    assert "Harvard" in text and "not distributed" in text


def test_default_out_is_anchored_to_repo():
    assert build_mod.DEFAULT_OUT == ROOT.parent / "site" / "public" / "data"


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
    monkeypatch.setattr(build_mod, "default_mask", fake_mask)
    monkeypatch.setattr(build_mod, "load_sources", lambda p: [SRC, UNVERIFIED])
    assert main(["build", "--out", str(tmp_path / "o"), "--cache", str(tmp_path / "c"), "--lessons", str(LESSONS)]) == 0
    assert main(["build", "--deploy", "--out", str(tmp_path / "o"), "--cache", str(tmp_path / "c"), "--lessons", str(LESSONS)]) == 1
