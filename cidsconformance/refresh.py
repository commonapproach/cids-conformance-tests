"""Download the latest published shapes, contexts and codelists."""

from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from .reference import (
    CODELIST_BASE_URL, CODELISTS, CONTEXT_URLS, EXTRA_REFERENCE_FILES, REFERENCE_DIR, SHAPES, SHAPES_URLS,
)


def _fetch(url: str, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 - fixed https URLs
        data = resp.read()
    if not data:
        raise RuntimeError(f"{url} returned an empty file")
    changed = not dest.exists() or dest.read_bytes() != data
    dest.write_bytes(data)
    return f"{'updated  ' if changed else 'unchanged'} {dest.name}  <- {url}"


def refresh(dest: Path | None = None) -> list[str]:
    dest = dest or REFERENCE_DIR
    log = []
    for profile, rel in SHAPES.items():
        log.append(_fetch(SHAPES_URLS[profile], dest / rel))
    for url, rel in CONTEXT_URLS.items():
        log.append(_fetch(url, dest / rel))
    for name in CODELISTS:
        log.append(_fetch(f"{CODELIST_BASE_URL}/{name}.ttl", dest / "codelists" / f"{name}.ttl"))
    # Not published online: carry over the pinned copy.
    for name in EXTRA_REFERENCE_FILES:
        src, target = REFERENCE_DIR / "codelists" / name, dest / "codelists" / name
        if src.resolve() != target.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
        log.append(f"kept      {name} (not published online; pinned copy from the CIDS repo)")
    return log
