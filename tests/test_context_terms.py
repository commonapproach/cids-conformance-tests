"""Every key in every capsule means something.

A JSON-LD processor silently drops keys that the context doesn't define, so
a typo (or a property the CIDS context lacks, such as ``forTarget``) would
quietly vanish from the graph instead of failing. Every key must be a
JSON-LD keyword, a term from the CIDS/SFF contexts, a prefixed name using a
prefix those contexts define (e.g. ``cids:forTarget``), or a full IRI.
"""

import json
from pathlib import Path

import pytest

from cidsconformance.reference import CONTEXT_URLS, context_document

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted((ROOT / "capsules").glob("*/*/*.jsonld")) + sorted((ROOT / "examples").glob("**/*.jsonld"))


def _context_terms() -> tuple[set[str], set[str]]:
    terms, prefixes = set(), set()
    for url in CONTEXT_URLS:
        for k, v in context_document(url)["@context"].items():
            if k.startswith("@"):
                continue
            terms.add(k)
            if isinstance(v, str) and v.endswith(("#", "/")):
                prefixes.add(k)
    return terms, prefixes


TERMS, PREFIXES = _context_terms()


def _keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "@context":
                continue
            yield k
            yield from _keys(v)
    elif isinstance(x, list):
        for v in x:
            yield from _keys(v)


@pytest.mark.parametrize("path", FILES, ids=[f"{p.parent.name}/{p.name}" for p in FILES])
def test_every_key_is_defined(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    unknown = sorted({k for k in _keys(data)
                      if not k.startswith("@") and k not in TERMS and "://" not in k
                      and not (":" in k and k.split(":", 1)[0] in PREFIXES)})
    assert not unknown, f"keys the JSON-LD context doesn't define (they would be dropped): {unknown}"
