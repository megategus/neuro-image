"""Per-region share of a prepared map's positive signal."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .atlas import ReferenceAtlas
from .prepare import PreparedMap


@dataclass
class Profile:
    map_id: str
    quantity: Literal["intensity_share", "voxel_share"]
    share: dict[str, float]
    size_normalised: dict[str, float]
    unassigned: float


def compute_profile(pm: PreparedMap, atlas: ReferenceAtlas) -> Profile:
    quantity = "voxel_share" if pm.source.threshold_type == "statistical" else "intensity_share"
    pos = np.asarray(pm.positive.dataobj, dtype=np.float64)
    lab = np.rint(np.asarray(atlas.img.dataobj)).astype(np.int32)
    if pos.shape != lab.shape:
        raise ValueError(f"map shape {pos.shape} does not match atlas shape {lab.shape}")

    values = (pos > 0).astype(np.float64) if quantity == "voxel_share" else np.where(pos > 0, pos, 0.0)
    total = float(values.sum())
    if total <= 0:
        raise ValueError(f"map {pm.source.id!r} has no positive signal")

    labelled = sum(int((lab == k).sum()) for k in atlas.labels)
    share: dict[str, float] = {}
    size_norm: dict[str, float] = {}
    for k, name in atlas.labels.items():
        mask = lab == k
        share[name] = float(values[mask].sum()) / total
        n = int(mask.sum())
        if n > 0:
            size_norm[name] = share[name] / (n / labelled)
    return Profile(
        map_id=pm.source.id,
        quantity=quantity,
        share=share,
        size_normalised=size_norm,
        unassigned=max(0.0, 1.0 - sum(share.values())),
    )
