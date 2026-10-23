"""Map metadata, threshold labels and lesson validation."""
from __future__ import annotations

from .sources import Source

DISPLAY_ONLY_LABEL = "display threshold chosen by the authors — not a significance test"
TODO_MARK = "TODO"  # deploy fails on any text field containing this substring
VIEWS = {"overlay", "profile", "both"}
_REQUIRED = ("citation", "doi", "n_studies", "method", "value_meaning",
             "threshold_type", "licence", "caveat")


def threshold_label(source: Source) -> str:
    if source.threshold_type == "display-only":
        return DISPLAY_ONLY_LABEL
    if source.threshold_type == "statistical":
        return f"statistical threshold reported by the authors: {source.threshold}"
    return "unthresholded — all values shown"


def _missing(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def check_completeness(maps: list[dict], for_deploy: bool) -> list[str]:
    problems: list[str] = []
    for m in maps:
        mid = m.get("id", "<unknown>")
        fields = list(_REQUIRED)
        if m.get("threshold_type") != "none":
            fields.append("threshold")
        for f in fields:
            if _missing(m.get(f)):
                problems.append(f"map {mid!r}: missing {f}")
        if for_deploy:
            for f, v in m.items():
                if isinstance(v, str) and TODO_MARK in v:
                    problems.append(f"map {mid!r}: {f} still contains {TODO_MARK}")
            if m.get("caveat_reviewed") is not True:
                problems.append(
                    f"map {mid!r}: caveat not yet medically reviewed "
                    "(set caveat_reviewed: true in sources.yaml after review)"
                )
    return problems


def _texts(les: dict) -> list[str]:
    out = [les.get("title"), les.get("notice")]
    out += les.get("body") if isinstance(les.get("body"), list) else []
    claims = les.get("claims") if isinstance(les.get("claims"), list) else []
    out += [c.get("text") for c in claims if isinstance(c, dict)]
    return [t for t in out if isinstance(t, str)]


def validate_lessons(
    lessons: dict,
    map_ids: set[str],
    for_deploy: bool = False,
    available_ids: set[str] | None = None,
) -> list[str]:
    """Problems in a lessons document.

    `map_ids` is every source id, built or not. `available_ids` is the set of
    verified (published) map ids: on deploy, an unreviewed lesson fails only if
    all of its maps are available, since otherwise the site does not show its
    text. With `available_ids=None` every known map counts as available.
    """
    problems: list[str] = []
    if not isinstance(lessons, dict):
        return ["lessons: top level must be an object"]
    if "reviewed" in lessons:
        problems.append("lessons: top-level 'reviewed' is replaced by a 'reviewed' flag on each lesson")
    available = map_ids if available_ids is None else available_ids
    items = lessons.get("lessons")
    if not isinstance(items, list):
        return problems + ["lessons: 'lessons' must be a list"]
    seen: set[str] = set()
    for i, les in enumerate(items):
        lid = les.get("id") if isinstance(les, dict) else None
        name = f"lesson {lid!r}" if isinstance(lid, str) and lid else f"lesson #{i}"
        if not isinstance(les, dict):
            problems.append(f"{name}: must be an object")
            continue
        if not isinstance(lid, str) or not lid:
            problems.append(f"{name}: missing id")
        elif lid in seen:
            problems.append(f"{name}: duplicate id")
        else:
            seen.add(lid)
        if not isinstance(les.get("title"), str) or not les["title"].strip():
            problems.append(f"{name}: missing title")
        ids = les.get("map_ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(x, str) for x in ids):
            problems.append(f"{name}: map_ids must be a non-empty list of strings")
        else:
            for x in ids:
                if x not in map_ids:
                    problems.append(f"{name}: unknown map id {x!r}")
        reviewed = les.get("reviewed")
        if not isinstance(reviewed, bool):
            problems.append(f"{name}: 'reviewed' must be true or false")
        elif (for_deploy and not reviewed and isinstance(ids, list) and ids
              and all(x in available for x in ids)):
            problems.append(
                f"{name}: not yet medically reviewed and all its maps are available "
                "(set \"reviewed\": true on this lesson after review)"
            )
        if les.get("view") not in VIEWS:
            problems.append(f"{name}: view must be one of {sorted(VIEWS)}")
        body = les.get("body")
        if not isinstance(body, list) or not body or not all(isinstance(x, str) and x.strip() for x in body):
            problems.append(f"{name}: body must be a non-empty list of strings")
        notice = les.get("notice")
        if not isinstance(notice, str) or not notice.strip():
            problems.append(f"{name}: missing notice")
        claims = les.get("claims")
        if not isinstance(claims, list):
            problems.append(f"{name}: claims must be a list")
            claims = []
        for j, c in enumerate(claims):
            if not isinstance(c, dict) or _missing(c.get("text")):
                problems.append(f"{name}: claim #{j} missing text")
            elif _missing(c.get("source_doi")):
                problems.append(f"{name}: claim #{j} has no source_doi")
        if for_deploy and any(TODO_MARK in t for t in _texts(les)):
            problems.append(f"{name}: still contains {TODO_MARK} text")
    return problems
