from pathlib import Path

import pytest

SOURCES_YAML = Path(__file__).resolve().parent.parent / "sources.yaml"


@pytest.fixture
def sources_yaml() -> Path:
    return SOURCES_YAML


def make_img(shape, affine, data):
    import nibabel as nib
    import numpy as np

    return nib.Nifti1Image(np.asarray(data, dtype=np.float32).reshape(shape), np.asarray(affine, dtype=float))


MNI_2MM = [[-2, 0, 0, 90], [0, 2, 0, -126], [0, 0, 2, -72], [0, 0, 0, 1]]
