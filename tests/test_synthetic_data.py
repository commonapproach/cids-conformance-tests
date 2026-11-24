"""Guards for the "synthetic data only" rule: every organization-specific
IRI and email uses a reserved .example domain, and business numbers can't
be real."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted((ROOT / "capsules").glob("*/*/*.jsonld")) + sorted((ROOT / "examples").glob("**/*.jsonld"))

# Shared reference vocabularies. Anything else must be on a .example domain.
ALLOWED_HOSTS = {
    "ontology.commonapproach.org",
    "codelist.commonapproach.org",
    "metadata.un.org",
}


def _strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


@pytest.mark.parametrize("path", FILES, ids=[f"{p.parent.name}/{p.name}" for p in FILES])
def test_only_fictional_domains(path):
    bad = set()
    for s in _strings(json.loads(path.read_text(encoding="utf-8"))):
        for host in re.findall(r"^[a-z]+://([^/:?#]+)", s):
            if host not in ALLOWED_HOSTS and not host.endswith(".example"):
                bad.add(host)
        for email_host in re.findall(r"[\w.+-]+@([\w.-]+)", s):
            if not email_host.endswith(".example"):
                bad.add(email_host)
        if s.startswith("tag:") and ".example," not in s:
            bad.add(s)
    assert not bad, f"non-fictional domains in {path.name}: {sorted(bad)}"


@pytest.mark.parametrize("path", FILES, ids=[f"{p.parent.name}/{p.name}" for p in FILES])
def test_business_numbers_cannot_be_real(path):
    for s in _strings(json.loads(path.read_text(encoding="utf-8"))):
        m = re.match(r"^(\d{9})\s*RC\d{4}", s)
        if m:
            assert not _luhn_ok(m.group(1)), f"{s} passes the CRA check digit; use a number that fails it"
