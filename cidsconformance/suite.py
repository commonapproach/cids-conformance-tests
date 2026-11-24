"""Check every capsule against its ``expected.json``.

For each capsule file this checks that:

* the SHACL results for the Basic tier and SFF shapes are exactly the
  expected ones (matched on severity, focus node, path and constraint),
* the data-quality findings are exactly the expected ones (when listed),
* the Turtle copy holds the same graph as the JSON-LD file.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from rdflib.compare import isomorphic

from .build import CAPSULES_DIR
from .dq import run_checks
from .load import load_graph
from .shacl import validate


@dataclass
class FileOutcome:
    capsule: str
    file: str
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _diff(label: str, expected: list[tuple], actual: list[tuple]) -> list[str]:
    exp, act = Counter(expected), Counter(actual)
    out = []
    for k in sorted(exp - act):
        out.append(f"{label}: expected but not reported: {k}")
    for k in sorted(act - exp):
        out.append(f"{label}: reported but not expected: {k}")
    return out


def check_capsule(capsule_dir: Path) -> list[FileOutcome]:
    spec = json.loads((capsule_dir / "expected.json").read_text(encoding="utf-8"))
    outcomes = []
    for name, exp in spec["files"].items():
        oc = FileOutcome(spec["id"], name)
        g = load_graph(capsule_dir / name)

        ttl = capsule_dir / name.replace(".jsonld", ".ttl")
        if not ttl.exists():
            oc.problems.append(f"missing Turtle copy {ttl.name}")
        elif not isomorphic(g, load_graph(ttl)):
            oc.problems.append(f"{ttl.name} does not hold the same graph as {name}")

        for profile, expected in exp["shacl"].items():
            want = [(r["severity"], r["focusNode"], r["resultPath"], r["sourceConstraintComponent"]) for r in expected]
            got = [r.key() for r in validate(g, profile)]
            oc.problems += _diff(f"SHACL {profile}", want, got)

        if exp["dq"] is not None:
            want = [(d["code"], d["focusNode"], d["resultPath"]) for d in exp["dq"]]
            got = [d.key() for d in run_checks(g)]
            oc.problems += _diff("DQ", want, got)
        outcomes.append(oc)
    return outcomes


def capsule_dirs(root: Path = CAPSULES_DIR, only: list[str] | None = None) -> list[Path]:
    dirs = sorted(p.parent for p in root.glob("*/*/expected.json"))
    if only:
        dirs = [d for d in dirs if any(o in d.name or o == d.parent.name for o in only)]
    return dirs


def run_suite(only: list[str] | None = None, root: Path = CAPSULES_DIR) -> list[FileOutcome]:
    results = []
    for d in capsule_dirs(root, only):
        results += check_capsule(d)
    return results
