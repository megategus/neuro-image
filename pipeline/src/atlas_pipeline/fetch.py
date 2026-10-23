"""Download a source map into a local cache, verifying its checksum."""
from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .sources import Source


class FetchError(Exception):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(source: Source, cache_dir: Path) -> Path:
    if source.status != "verified":
        raise FetchError(f"source {source.id!r} is unverified; refusing to fetch")
    name = Path(urlparse(source.url).path).name
    if not name:
        raise FetchError(f"source {source.id!r}: cannot derive a file name from {source.url}")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / name

    if not dest.exists():
        fd, tmp_name = tempfile.mkstemp(dir=cache_dir, suffix=".part")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as out, urllib.request.urlopen(source.url, timeout=60) as resp:
                while chunk := resp.read(1 << 20):
                    out.write(chunk)
            tmp.replace(dest)
        except (urllib.error.URLError, OSError) as e:
            tmp.unlink(missing_ok=True)
            raise FetchError(f"source {source.id!r}: download failed: {e}") from e

    if source.sha256 is not None:
        actual = _sha256(dest)
        if actual != source.sha256:
            raise FetchError(
                f"source {source.id!r}: sha256 mismatch for {dest} (expected {source.sha256}, got {actual})"
            )
    return dest
