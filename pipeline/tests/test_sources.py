import pytest
import yaml

from atlas_pipeline.sources import load_sources


def test_load_sources_reads_all_seven(sources_yaml):
    sources = load_sources(sources_yaml)
    assert len(sources) == 7
    emotions = [s for s in sources if s.group == "emotion"]
    assert len(emotions) == 5
    assert {s.study_id for s in emotions} == {"wager2015"}


def test_load_sources_rejects_missing_doi(sources_yaml, tmp_path):
    data = yaml.safe_load(sources_yaml.read_text())
    del data["sources"][2]["doi"]
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError) as exc:
        load_sources(bad)
    assert data["sources"][2]["id"] in str(exc.value)
    assert "doi" in str(exc.value)
