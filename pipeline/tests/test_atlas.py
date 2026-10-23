from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from atlas_pipeline import atlas as atlas_mod
from atlas_pipeline.atlas import build_reference_atlas, network_for_component, parse_lut
from atlas_pipeline.prepare import target_grid

LUT = """\
  0   Background 0 0 0 0
  1   7Networks_LH_Vis_1 120 18 134 0
  6   7Networks_LH_SalVentAttn_ParOper 196 58 250 0
  9   7Networks_RH_Default_PFCm_1 205 62 78 0
"""


def test_parse_lut_and_network_mapping():
    lut = parse_lut(LUT)
    assert lut[6] == "7Networks_LH_SalVentAttn_ParOper"
    assert 0 not in lut
    assert network_for_component(lut[1]) == 1
    assert network_for_component(lut[6]) == 4
    assert network_for_component(lut[9]) == 7


def test_unknown_network_token_raises():
    with pytest.raises(ValueError):
        network_for_component("7Networks_LH_Bogus_1")


@pytest.mark.network
def test_atlas_has_eleven_named_labels():
    cache = Path(__file__).resolve().parent.parent / ".cache"
    ref = build_reference_atlas(target_grid(), cache)
    assert sorted(ref.labels) == list(range(1, 12))
    assert ref.labels[1] == "Visual" and ref.labels[11] == "Brainstem"
    data = np.asarray(ref.img.dataobj)
    assert set(np.unique(data)) <= set(range(12))
    for k in range(1, 12):
        assert (data == k).any(), k
    assert [s["bundled"] for s in ref.sources] == [True, False]
