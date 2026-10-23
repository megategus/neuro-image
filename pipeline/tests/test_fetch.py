import dataclasses
import hashlib
import urllib.request

import pytest

from atlas_pipeline.fetch import FetchError, fetch
from atlas_pipeline.sources import load_sources


def _boom(*a, **k):
    raise AssertionError("network used")


@pytest.fixture
def fear(sources_yaml):
    return next(s for s in load_sources(sources_yaml) if s.id == "fear")


def _cached_name(source):
    return source.url.rsplit("/", 1)[-1]


def test_fetch_uses_cache(fear, tmp_path, monkeypatch):
    (tmp_path / _cached_name(fear)).write_bytes(b"data")
    fear = dataclasses.replace(fear, sha256=None)
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    path = fetch(fear, tmp_path)
    assert path.read_bytes() == b"data"


def test_fetch_accepts_matching_checksum(fear, tmp_path, monkeypatch):
    (tmp_path / _cached_name(fear)).write_bytes(b"data")
    fear = dataclasses.replace(fear, sha256=hashlib.sha256(b"data").hexdigest())
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    assert fetch(fear, tmp_path).exists()


def test_fetch_rejects_checksum_mismatch(fear, tmp_path, monkeypatch):
    (tmp_path / _cached_name(fear)).write_bytes(b"data")
    fear = dataclasses.replace(fear, sha256="0" * 64)
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(FetchError, match="sha256"):
        fetch(fear, tmp_path)


def test_unverified_source_not_fetched_by_default(sources_yaml, tmp_path, monkeypatch):
    anxiety = next(s for s in load_sources(sources_yaml) if s.id == "anxiety")
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(FetchError, match="unverified"):
        fetch(anxiety, tmp_path)
