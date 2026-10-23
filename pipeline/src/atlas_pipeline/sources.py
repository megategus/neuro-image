"""Registry of published meta-analytic maps (pipeline/sources.yaml)."""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal

import yaml


@dataclass(frozen=True)
class Source:
    id: str
    label: str
    group: Literal["emotion", "anxiety", "retrieval"]
    study_id: str  # colour-scale grouping key
    url: str
    sha256: str | None
    status: Literal["verified", "unverified"]
    citation: str
    doi: str
    n_studies: int | None
    method: str
    value_meaning: str
    threshold: float | None
    threshold_type: Literal["statistical", "display-only", "none"]
    licence: str
    caveat: str
    # True only once the medical reviewer has approved `caveat` (deploy gate).
    caveat_reviewed: bool = False


_OPTIONAL = {"sha256", "n_studies", "threshold"}
_GROUPS = {"emotion", "anxiety", "retrieval"}
_STATUSES = {"verified", "unverified"}
_THRESHOLD_TYPES = {"statistical", "display-only", "none"}


def load_sources(path: Path) -> list[Source]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    entries = (data or {}).get("sources")
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected a top-level 'sources' list")
    names = [f.name for f in fields(Source)]
    sources: list[Source] = []
    for i, entry in enumerate(entries):
        sid = entry.get("id", f"<entry {i}>")
        for name in names:
            if name not in entry:
                raise ValueError(f"source {sid!r}: missing field {name!r}")
            if entry[name] is None and name not in _OPTIONAL:
                raise ValueError(f"source {sid!r}: field {name!r} must not be null")
        for name, allowed in (
            ("group", _GROUPS),
            ("status", _STATUSES),
            ("threshold_type", _THRESHOLD_TYPES),
        ):
            if entry[name] not in allowed:
                raise ValueError(
                    f"source {sid!r}: field {name!r} must be one of {sorted(allowed)}, got {entry[name]!r}"
                )
        if not isinstance(entry["caveat_reviewed"], bool):
            raise ValueError(f"source {sid!r}: field 'caveat_reviewed' must be true or false")
        sources.append(Source(**{n: entry[n] for n in names}))
    return sources
