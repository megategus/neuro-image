"""Reference atlas: Yeo 7 networks plus Harvard-Oxford subcortical regions."""
from __future__ import annotations

import csv
import warnings
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn.image import resample_to_img

from .fetch import download
from .prepare import _same_grid

_YEO_DIR = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/master/stable_projects/"
    "brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/"
    "Yeo_JNeurophysiol11_SplitLabels/MNI152/"
)
YEO_IMG_URL = _YEO_DIR + "Yeo2011_7Networks_N1000.split_components.FSL_MNI152_2mm.nii.gz"
YEO_LUT_URL = _YEO_DIR + "7Networks_ColorLUT_freeview.txt"
_TF = "https://templateflow.s3.amazonaws.com/tpl-MNI152NLin6Asym/"
HO_IMG_URL = _TF + "tpl-MNI152NLin6Asym_res-02_atlas-HOSPA_desc-th25_dseg.nii.gz"
HO_TSV_URL = _TF + "tpl-MNI152NLin6Asym_atlas-HOSPA_dseg.tsv"

NETWORKS = {
    "Vis": 1, "SomMot": 2, "DorsAttn": 3, "SalVentAttn": 4,
    "Limbic": 5, "Cont": 6, "Default": 7,
}
LABELS = {
    1: "Visual", 2: "Somatomotor", 3: "Dorsal attention",
    4: "Ventral attention/salience", 5: "Limbic", 6: "Frontoparietal control",
    7: "Default mode", 8: "Amygdala", 9: "Hippocampus", 10: "Thalamus", 11: "Brainstem",
}
_HO_NAMES = {"Amygdala": 8, "Hippocampus": 9, "Thalamus": 10, "Brainstem": 11}

SOURCES = [
    {
        "name": "Yeo 2011 7-network parcellation (CBIG split components)",
        "citation": "Yeo BTT et al. (2011) J Neurophysiol 106:1125–1165. doi:10.1152/jn.00338.2011",
        "licence": "MIT (CBIG)",
        "bundled": True,
    },
    {
        "name": "Harvard–Oxford subcortical atlas (maxprob thr25, via TemplateFlow)",
        "citation": "Desikan RS et al. (2006) NeuroImage 31:968–980; FSL atlases",
        "licence": "FSL licence (non-commercial)",
        "bundled": False,
    },
]


@dataclass
class ReferenceAtlas:
    img: nib.Nifti1Image
    labels: dict[int, str]
    sources: list[dict]


def parse_lut(text: str) -> dict[int, str]:
    """Freeview colour LUT -> {index: name}; background (0) is dropped."""
    out: dict[int, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[0].startswith("#"):
            continue
        idx = int(parts[0])
        if idx != 0:
            out[idx] = parts[1]
    return out


def network_for_component(name: str) -> int:
    """'7Networks_LH_SalVentAttn_ParOper' -> 4. Unknown tokens raise ValueError."""
    parts = name.split("_")
    token = parts[2] if len(parts) > 2 else ""
    if token not in NETWORKS:
        raise ValueError(f"unknown Yeo network token {token!r} in component {name!r}")
    return NETWORKS[token]


def _cached(url: str, cache_dir: Path) -> Path:
    dest = Path(cache_dir) / url.rsplit("/", 1)[1]
    if not dest.exists():
        download(url, dest)
    return dest


def _to_target(img: nib.Nifti1Image, target: nib.Nifti1Image) -> np.ndarray:
    if _same_grid(img, target):
        return np.rint(np.asarray(img.dataobj)).astype(np.int32)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Resampling binary images")
        out = resample_to_img(
            img, target, interpolation="nearest", force_resample=True, copy_header=True
        )
    return np.rint(np.asarray(out.dataobj)).astype(np.int32)


def build_reference_atlas(target: nib.Nifti1Image, cache_dir: Path) -> ReferenceAtlas:
    cache_dir = Path(cache_dir)
    yeo_img = nib.load(_cached(YEO_IMG_URL, cache_dir))
    lut = parse_lut(_cached(YEO_LUT_URL, cache_dir).read_text(encoding="utf-8"))
    ho_img = nib.load(_cached(HO_IMG_URL, cache_dir))
    with _cached(HO_TSV_URL, cache_dir).open(encoding="utf-8", newline="") as f:
        ho_names = {int(r["index"]): r["name"] for r in csv.DictReader(f, delimiter="\t")}

    yeo = _to_target(yeo_img, target)
    out = np.zeros(yeo.shape, dtype=np.int32)
    for comp in np.unique(yeo):
        if comp == 0:
            continue
        if int(comp) not in lut:
            raise ValueError(f"Yeo component {int(comp)} missing from label table")
        out[yeo == comp] = network_for_component(lut[int(comp)])

    ho = _to_target(ho_img, target)
    found = set()
    for idx, name in ho_names.items():
        base = name
        for prefix in ("Left ", "Right "):
            if base.startswith(prefix):
                base = base[len(prefix):]
        if base in _HO_NAMES:
            found.add(base)
            out[ho == idx] = _HO_NAMES[base]
    if found != set(_HO_NAMES):
        raise ValueError(f"Harvard-Oxford labels not found: {sorted(set(_HO_NAMES) - found)}")

    img = nib.Nifti1Image(out.astype(np.int16), target.affine)
    img.set_data_dtype(np.int16)
    return ReferenceAtlas(img=img, labels=dict(LABELS), sources=[dict(s) for s in SOURCES])
