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


def test_caveat_reviewed_loaded_and_all_false(sources_yaml):
    sources = load_sources(sources_yaml)
    assert all(s.caveat_reviewed is False for s in sources)


def test_load_sources_rejects_non_bool_caveat_reviewed(sources_yaml, tmp_path):
    data = yaml.safe_load(sources_yaml.read_text())
    data["sources"][0]["caveat_reviewed"] = "yes"
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="caveat_reviewed"):
        load_sources(bad)


def test_load_sources_requires_caveat_reviewed(sources_yaml, tmp_path):
    data = yaml.safe_load(sources_yaml.read_text())
    del data["sources"][0]["caveat_reviewed"]
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="caveat_reviewed"):
        load_sources(bad)
