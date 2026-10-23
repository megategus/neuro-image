"""`build`: fetch, verify, prepare and write every published data file."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import nibabel as nib
import numpy as np

from .atlas import ReferenceAtlas, build_reference_atlas
from .fetch import FetchError, fetch
from .fetch import download
from .metadata import check_completeness, threshold_label, validate_lessons
from .notices import MNI_NOTICE, notices_text
from .prepare import PreparedMap, background_template, prepare, target_grid
from .profile import compute_profile
from .sources import Source, load_sources
from .verify import verify

PIPELINE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT = PIPELINE_DIR.parent / "site" / "public" / "data"
DEFAULT_CACHE = PIPELINE_DIR / ".cache"
DEFAULT_SOURCES = PIPELINE_DIR / "sources.yaml"
DEFAULT_LESSONS = PIPELINE_DIR / "lessons" / "lessons.json"

TEMPLATE_INFO = {
    "name": "MNI ICBM152 non-linear 2009 template (bundled with nilearn), resampled to FSL 2 mm grid",
    "licence": "MNI ICBM152 licence (permissive; copyright notice must appear in all copies): "
               "Copyright (C) 1993-2004 Louis Collins, McConnell Brain Imaging Centre, "
               "Montreal Neurological Institute, McGill University",
    "notice": MNI_NOTICE,
}
# Brain mask used by verify() to judge whether a map is pre-thresholded.
MASK_URL = (
    "https://templateflow.s3.amazonaws.com/tpl-MNI152NLin6Asym/"
    "tpl-MNI152NLin6Asym_res-02_desc-brain_mask.nii.gz"
)
# Atlas label -> index into ReferenceAtlas.sources (Yeo 1-7, Harvard-Oxford 8-11).
_LABEL_SOURCE = {**{k: 0 for k in range(1, 8)}, **{k: 1 for k in range(8, 12)}}

def load_brain_mask(cache_dir: Path) -> nib.Nifti1Image:
    dest = Path(cache_dir) / MASK_URL.rsplit("/", 1)[1]
    if not dest.exists():
        download(MASK_URL, dest)
    loaded = nib.load(dest)
    return nib.Nifti1Image(np.asarray(loaded.dataobj), loaded.affine)


default_fetch = fetch
default_atlas = build_reference_atlas
default_mask = load_brain_mask


def _r(x):
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: _r(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_r(v) for v in x]
    return x


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(_r(obj), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _save(img: nib.Nifti1Image, path: Path, dtype) -> None:
    out = nib.Nifti1Image(np.asarray(img.dataobj).astype(dtype), img.affine)
    out.set_data_dtype(dtype)
    nib.save(out, path)


def _entry(pm: PreparedMap) -> dict:
    s = pm.source
    return {
        "id": s.id, "label": s.label, "group": s.group, "study_id": s.study_id,
        "citation": s.citation, "doi": s.doi, "n_studies": s.n_studies, "method": s.method,
        "value_meaning": s.value_meaning, "threshold": s.threshold,
        "threshold_type": s.threshold_type, "threshold_label": threshold_label(s),
        "licence": s.licence, "caveat": s.caveat, "caveat_reviewed": s.caveat_reviewed,
        "display_min": pm.display_min, "display_max": pm.display_max,
        "has_negative": pm.negative is not None,
        "files": {
            "pos": f"maps/{s.id}_pos.nii.gz",
            "neg": f"maps/{s.id}_neg.nii.gz" if pm.negative is not None else None,
        },
    }


def run_build(
    sources: list[Source],
    lessons_path: Path,
    out: Path,
    cache_dir: Path,
    deploy: bool = False,
    fetch_fn: Callable = default_fetch,
    atlas_fn: Callable = default_atlas,
    mask_fn: Callable = default_mask,
) -> list[str]:
    """Write all outputs to `out`; return the list of problems (empty on success)."""
    problems: list[str] = []
    out, cache_dir = Path(out), Path(cache_dir)
    (out / "maps").mkdir(parents=True, exist_ok=True)
    target = target_grid()

    try:
        lessons = json.loads(Path(lessons_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"lessons: cannot read {lessons_path}: {e}"]
    verified_ids = {s.id for s in sources if s.status == "verified"}
    problems += validate_lessons(lessons, {s.id for s in sources}, for_deploy=deploy,
                                 available_ids=verified_ids)

    try:
        mask = mask_fn(cache_dir)
    except Exception as e:  # noqa: BLE001 - without a mask the thresholded check is meaningless
        problems.append(f"brain mask: {e}")
        mask = None

    try:
        ref: ReferenceAtlas | None = atlas_fn(target, cache_dir)
    except Exception as e:  # noqa: BLE001 - any atlas failure is a build error
        problems.append(f"atlas: {e}")
        ref = None

    prepared: list[PreparedMap] = []
    unavailable: list[dict] = []
    for s in sources:
        if s.status != "verified":
            unavailable.append({"id": s.id, "label": s.label, "reason": "source not yet verified"})
            continue
        try:
            img = nib.load(fetch_fn(s, cache_dir))
            report = verify(img, mask)
            if not report.ok:
                problems.append(f"map {s.id!r}: verification failed: " + "; ".join(report.problems))
                continue
            if mask is not None and report.is_thresholded and s.threshold_type != "statistical":
                # Spec 6.3: a map pre-thresholded at a cut the authors do not state is unusable.
                problems.append(
                    f"map {s.id!r}: looks pre-thresholded (over 30% of in-brain voxels are zero) "
                    f"but threshold_type is {s.threshold_type!r}; a pre-thresholded map needs the "
                    "authors' stated statistical threshold, otherwise use the fallback source"
                )
                continue
            prepared.append(prepare(s, img, target))
        except (FetchError, OSError, ValueError) as e:
            problems.append(f"map {s.id!r}: {e}")

    entries = [_entry(pm) for pm in prepared]
    problems += check_completeness(entries, deploy)

    profiles = []
    if ref is not None:
        for pm in prepared:
            try:
                profiles.append(asdict(compute_profile(pm, ref)))
            except ValueError as e:
                problems.append(f"map {pm.source.id!r}: profile: {e}")

    for pm in prepared:
        _save(pm.positive, out / "maps" / f"{pm.source.id}_pos.nii.gz", np.float32)
        if pm.negative is not None:
            _save(pm.negative, out / "maps" / f"{pm.source.id}_neg.nii.gz", np.float32)
    _save(background_template(target), out / "template.nii.gz", np.float32)

    _write_json(out / "maps.json", {"maps": entries, "unavailable": unavailable})
    if ref is not None:
        keys = sorted(ref.labels)
        _write_json(out / "profiles.json",
                    {"regions": [ref.labels[k] for k in keys], "profiles": profiles})
        bundled = {k: bool(ref.sources[_LABEL_SOURCE[k]]["bundled"]) if _LABEL_SOURCE.get(k, -1) < len(ref.sources) else False
                   for k in keys}
        _write_json(out / "atlas.json", {
            "labels": {str(k): {"name": ref.labels[k], "displayable": bundled[k]} for k in keys},
            "sources": ref.sources,
            "template": TEMPLATE_INFO,
        })
        label_file = out / "atlas_labels.nii.gz"
        if any(bundled.values()):
            data = np.rint(np.asarray(ref.img.dataobj)).astype(np.int32)
            keep = np.isin(data, [k for k in keys if bundled[k]])
            _save(nib.Nifti1Image(np.where(keep, data, 0), ref.img.affine), label_file, np.uint8)
        else:
            label_file.unlink(missing_ok=True)
    if ref is not None:
        (out / "NOTICES.txt").write_text(
            notices_text(entries, ref.sources, TEMPLATE_INFO), encoding="utf-8")
    _write_json(out / "lessons.json", lessons)
    return problems


def run(deploy: bool, out: Path, cache: Path, sources_path: Path, lessons_path: Path) -> int:
    problems = run_build(load_sources(sources_path), lessons_path, out, cache, deploy=deploy,
                         fetch_fn=default_fetch, atlas_fn=default_atlas,
                         mask_fn=default_mask)
    for p in problems:
        print(f"ERROR: {p}")
    if problems:
        print(f"build failed with {len(problems)} problem(s)")
        return 1
    print(f"build ok -> {out}")
    return 0
