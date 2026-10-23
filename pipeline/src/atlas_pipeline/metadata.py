"""Map metadata, threshold labels and lesson validation."""
from __future__ import annotations

from .sources import Source

DISPLAY_ONLY_LABEL = "display threshold chosen by the authors — not a significance test"
TODO_CAVEAT = "TODO-caveat"
TODO_DRAFT = "TODO-draft"
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
        if for_deploy and m.get("caveat") == TODO_CAVEAT:
            problems.append(f"map {mid!r}: caveat is still {TODO_CAVEAT}")
    return problems


def validate_lessons(lessons: dict, map_ids: set[str], for_deploy: bool = False) -> list[str]:
    """Problems in a lessons document. `map_ids` is every source id, built or not."""
    problems: list[str] = []
    if not isinstance(lessons, dict):
        return ["lessons: top level must be an object"]
    if not isinstance(lessons.get("reviewed"), bool):
        problems.append("lessons: 'reviewed' must be true or false")
    elif for_deploy and not lessons["reviewed"]:
        problems.append("lessons: reviewed is false; lessons must be reviewed before deploy")
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
        if for_deploy:
            texts = (body if isinstance(body, list) else []) + [notice]
            if TODO_DRAFT in texts:
                problems.append(f"{name}: still contains {TODO_DRAFT}")
    return problems
