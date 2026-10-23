"""`inspect` subcommand: print a verification report for a local or remote map."""
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

import nibabel as nib
import numpy as np

from .fetch import download
from .verify import verify


MASK_URL = (
    "https://templateflow.s3.amazonaws.com/tpl-MNI152NLin6Asym/"
    "tpl-MNI152NLin6Asym_res-02_desc-brain_mask.nii.gz"
)
CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"


def _load_mask():
    dest = CACHE_DIR / Path(MASK_URL).name
    try:
        if not dest.exists():
            download(MASK_URL, dest)
        return nib.load(dest)
    except Exception as e:  # FetchError, corrupt file, ...
        print(f"warning: brain mask unavailable ({e}); thresholded check uses all finite voxels", file=sys.stderr)
        return None


def inspect(target: str) -> dict:
    mask = _load_mask()
    if target.startswith(("http://", "https://")):
        with tempfile.TemporaryDirectory() as d:
            name = Path(target.split("?")[0]).name or "image.nii.gz"
            loaded = nib.load(download(target, Path(d) / name))
            # materialise in memory: verify reads data after the temp file is removed
            img = nib.Nifti1Image(np.asarray(loaded.dataobj), loaded.affine)
            return asdict(verify(img, mask))
    return asdict(verify(nib.load(target), mask))


def run(target: str) -> int:
    print(json.dumps(inspect(target), indent=2))
    return 0
