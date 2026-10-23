"""`inspect` subcommand: print a verification report for a local or remote map."""
from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path

import nibabel as nib
import numpy as np

from .fetch import download
from .verify import verify


def inspect(target: str) -> dict:
    if target.startswith(("http://", "https://")):
        with tempfile.TemporaryDirectory() as d:
            name = Path(target.split("?")[0]).name or "image.nii.gz"
            loaded = nib.load(download(target, Path(d) / name))
            # materialise in memory: verify reads data after the temp file is removed
            img = nib.Nifti1Image(np.asarray(loaded.dataobj), loaded.affine)
            return asdict(verify(img))
    return asdict(verify(nib.load(target)))


def run(target: str) -> int:
    print(json.dumps(inspect(target), indent=2))
    return 0
