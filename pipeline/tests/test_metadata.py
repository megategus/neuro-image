import json
from dataclasses import replace
from pathlib import Path

from atlas_pipeline.metadata import (
    DISPLAY_ONLY_LABEL,
    check_completeness,
    threshold_label,
    validate_lessons,
)
from atlas_pipeline.sources import load_sources

IDS = {"fear", "anxiety"}
LESSONS_JSON = Path(__file__).resolve().parent.parent / "lessons" / "lessons.json"


def lesson(**kw):
    base = {"id": "a", "title": "T", "map_ids": ["fear"], "view": "overlay",
            "body": ["text"], "notice": "look", "claims": []}
    base.update(kw)
    return base


def doc(*lessons, reviewed=True):
    return {"reviewed": reviewed, "lessons": list(lessons)}


def test_display_only_label_text_is_verbatim():
    src = load_sources(Path(__file__).resolve().parent.parent / "sources.yaml")[0]
    assert threshold_label(src) == (
        "display threshold chosen by the authors — not a significance test"
    )
    assert DISPLAY_ONLY_LABEL == threshold_label(src)


def test_threshold_labels_other_types():
    src = load_sources(Path(__file__).resolve().parent.parent / "sources.yaml")[0]
    assert threshold_label(replace(src, threshold_type="statistical", threshold=0.05)) == \
        "statistical threshold reported by the authors: 0.05"
    assert threshold_label(replace(src, threshold_type="none", threshold=None)) == \
        "unthresholded — all values shown"


def test_valid_lesson_passes():
    assert validate_lessons(doc(lesson()), IDS, for_deploy=True) == []


def test_unknown_map_id_in_lesson_fails():
    problems = validate_lessons(doc(lesson(map_ids=["fear", "nope"])), IDS)
    assert any("nope" in p for p in problems)


def test_lesson_claim_without_doi_fails():
    problems = validate_lessons(doc(lesson(claims=[{"text": "x", "source_doi": ""}])), IDS)
    assert any("source_doi" in p for p in problems)


def test_bad_structure_fails():
    assert validate_lessons(doc(lesson(view="3d")), IDS)
    assert validate_lessons(doc(lesson(body=[])), IDS)
    assert validate_lessons(doc(lesson(), lesson()), IDS)  # duplicate id
    assert validate_lessons({"reviewed": "yes", "lessons": []}, IDS)


def test_deploy_fails_when_unreviewed():
    d = doc(lesson(), reviewed=False)
    assert any("reviewed" in p for p in validate_lessons(d, IDS, for_deploy=True))


def test_local_build_allows_unreviewed():
    assert validate_lessons(doc(lesson(), reviewed=False), IDS, for_deploy=False) == []


def test_todo_draft_fails_only_for_deploy():
    d = doc(lesson(body=["TODO-draft"], notice="TODO-draft"))
    assert validate_lessons(d, IDS) == []
    assert any("TODO-draft" in p for p in validate_lessons(d, IDS, for_deploy=True))


def test_shipped_placeholder_lessons_are_valid_locally():
    sources = load_sources(Path(__file__).resolve().parent.parent / "sources.yaml")
    d = json.loads(LESSONS_JSON.read_text(encoding="utf-8"))
    assert [l["id"] for l in d["lessons"]] == [
        "reading-maps", "five-emotions", "fear-vs-anxiety", "retrieval-dmn", "fear-vs-retrieval"]
    assert validate_lessons(d, {s.id for s in sources}) == []


def entry(**kw):
    base = {"id": "m", "citation": "c", "doi": "d", "n_studies": 3, "method": "m",
            "value_meaning": "v", "threshold": 0.1, "threshold_type": "statistical",
            "licence": "l", "caveat": "real caveat"}
    base.update(kw)
    return base


def test_completeness_missing_field_always_fails():
    assert check_completeness([entry(doi="")], False)
    assert check_completeness([entry(citation=None)], False)
    assert check_completeness([entry(n_studies=None)], False)
    assert check_completeness([entry(threshold=None)], False)
    assert check_completeness([entry()], False) == []


def test_completeness_none_threshold_ok_for_type_none():
    assert check_completeness([entry(threshold=None, threshold_type="none")], False) == []


def test_completeness_todo_caveat_only_fails_on_deploy():
    e = entry(caveat="TODO-caveat")
    assert check_completeness([e], False) == []
    assert any("caveat" in p for p in check_completeness([e], True))
