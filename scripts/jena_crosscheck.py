"""Check the expected SHACL results with Apache Jena, the engine used by the
official CIDS-validate.sh script, instead of pyshacl.

Needs Jena's `shacl` command on your PATH (https://jena.apache.org/download/;
CI uses Jena 5.5.0, see .github/workflows/conformance.yml) and Java 17 or newer.
Run from the repository root:

    python scripts/jena_crosscheck.py

Data is prepared the same way as CIDS-validate.sh --codelists: capsule and
codelists merged into one data graph, and results on codelist nodes ignored.
Shapes are the same corrected copies the suite uses (only the Essential and
Full tier files need correcting; see cidsconformance/shape_fixes.py).
Jena relabels blank nodes, so a blank focus node (e.g. ".../2022 / i72:value")
is matched as "some blank node" plus its path and constraint.
"""

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.CRITICAL)

from rdflib import BNode, Graph, RDF  # noqa: E402

from cidsconformance.load import load_graph  # noqa: E402
from cidsconformance.reference import codelists_graph, shapes_graph  # noqa: E402
from cidsconformance.shacl import SH, describe_node, is_codelist_node, qname  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def jena_results(capsule: Graph, profile: str, workdir: Path) -> set:
    data = workdir / "data.nt"
    (capsule + codelists_graph()).serialize(data, format="nt", encoding="utf-8")
    # The same corrected shapes the suite uses (see cidsconformance/shape_fixes.py).
    shapes = workdir / f"shapes-{profile}.ttl"
    if not shapes.exists():
        shapes_graph(profile).serialize(shapes, format="turtle", encoding="utf-8")
    out = subprocess.run(["shacl", "validate", "--shapes", str(shapes), "--data", str(data)],
                         capture_output=True, text=True, check=True).stdout
    report = Graph().parse(data=out, format="turtle")
    subjects = set(capsule.subjects())
    got = set()
    for r in report.subjects(RDF.type, SH.ValidationResult):
        focus = report.value(r, SH.focusNode)
        if isinstance(focus, BNode):
            name = "BLANK"
        elif focus in subjects and not is_codelist_node(focus):
            name = describe_node(capsule, focus)
        else:
            continue
        got.add((qname(report.value(r, SH.resultSeverity)).replace("sh:", ""), name,
                 qname(report.value(r, SH.resultPath)), qname(report.value(r, SH.sourceConstraintComponent))))
    return got


def main() -> int:
    mismatches = 0
    with tempfile.TemporaryDirectory() as tmp:
        for exp_path in sorted(ROOT.glob("capsules/*/*/expected.json")):
            spec = json.loads(exp_path.read_text(encoding="utf-8"))
            for name, exp in spec["files"].items():
                capsule = load_graph(exp_path.parent / name)
                for profile in exp["shacl"]:
                    want = {(x["severity"], "BLANK" if " / " in x["focusNode"] else x["focusNode"],
                             x["resultPath"], x["sourceConstraintComponent"]) for x in exp["shacl"][profile]}
                    got = jena_results(capsule, profile, Path(tmp))
                    status = "ok  " if got == want else "DIFF"
                    print(f"{status} {spec['id']}/{name} [{profile}]")
                    if got != want:
                        mismatches += 1
                        for k in sorted(got - want):
                            print(f"       Jena only:     {k}")
                        for k in sorted(want - got):
                            print(f"       expected only: {k}")
    print(f"\n{mismatches} mismatch(es) between Jena and the expected results.")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
