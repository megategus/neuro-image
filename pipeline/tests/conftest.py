from pathlib import Path

import pytest

SOURCES_YAML = Path(__file__).resolve().parent.parent / "sources.yaml"


@pytest.fixture
def sources_yaml() -> Path:
    return SOURCES_YAML
