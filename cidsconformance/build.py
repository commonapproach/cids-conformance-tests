"""Write the capsules in ``capsules/`` from the definitions in
``generator/catalog.py``."""

from __future__ import annotations

import json
from pathlib import Path

from rdflib import Graph

from .generator.catalog import Capsule, all_capsules
from .generator.examples import EXAMPLES
from .load import graph_from_jsonld
from .reference import PROFILE_LABELS, REPO_ROOT
from .shacl import PREFIXES

CAPSULES_DIR = REPO_ROOT / "capsules"
EXAMPLES_DIR = REPO_ROOT / "examples" / "round-trip"
DOCS_DIR = REPO_ROOT / "docs"

CATEGORY_LABEL = {
    "valid": "Valid",
    "invalid": "Broken (fails SHACL)",
    "data-quality": "Data quality (passes SHACL, flagged by DQ checks)",
}


def to_turtle(g: Graph) -> str:
    out = Graph()
    for prefix in ("cids", "sff", "org", "i72", "prov", "foaf", "ic", "rdfs", "xsd", "schema"):
        out.bind(prefix, PREFIXES[prefix], override=True, replace=True)
    for t in g:
        out.add(t)
    return out.serialize(format="turtle")


def _json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def render_files(c: Capsule) -> dict[str, str]:
    """Every file for one capsule, as {relative path: content}."""
    files: dict[str, str] = {}
    for f in c.files:
        files[f.name] = _json(f.nodes)
        files[f.name.replace(".jsonld", ".ttl")] = to_turtle(graph_from_jsonld(f.nodes))
    files["expected.json"] = _json({
        "id": c.id,
        "category": c.category,
        "title": c.title,
        "files": c.expected(),
    })
    files["README.md"] = render_readme(c)
    return files


def _table(headers, rows) -> list[str]:
    def esc(s):
        return str(s).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(esc(x) for x in r) + " |" for r in rows]
    return out


def _profile_list(profiles) -> str:
    names = [PROFILE_LABELS[p] for p in profiles]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def render_readme(c: Capsule) -> str:
    source = f"Sample file `{c.source}` from the 2025 sample set" if c.source.endswith(".json") else c.source
    L = [f"# {c.id}: {c.title}", "", c.summary, "",
         f"**Category:** {CATEGORY_LABEL[c.category]}  ", f"**Based on:** {source}", ""]

    L += ["## Files", ""]
    for f in c.files:
        ttl = f.name.replace(".jsonld", ".ttl")
        desc = f" {f.description}" if f.description else ""
        L.append(f"- `{f.name}`: the capsule in JSON-LD.{desc} `{ttl}` has the same data in Turtle.")
    L.append("- `expected.json`: the expected validation results, in machine-readable form.")
    L.append("")

    if c.covers:
        L += ["## What it tests", ""] + [f"- {x}" for x in c.covers] + [""]
    if c.roundtrip:
        L += ["## What must come back unchanged after import and export", ""] + [f"- {x}" for x in c.roundtrip] + [""]

    L += ["## Expected validation result", ""]
    for f in c.files:
        if len(c.files) > 1:
            L += [f"### `{f.name}`", ""]
        if c.category == "valid":
            L.append(f"Passes {_profile_list(c.profiles)} SHACL validation with no results at all "
                     "(no violations, warnings or info), and the data-quality checks find nothing.")
            L.append("")
            if any(p in ("essential", "full") for p in c.profiles):
                L += ["The published Essential and Full tier shapes have bugs that make every capsule fail. "
                      "The tools correct them when loading the shapes; see "
                      "[reference/SOURCES.md](../../../reference/SOURCES.md#corrections-to-the-published-shapes).", ""]
            continue
        if f.shacl:
            rows = []
            for r in f.shacl:
                profiles = " + ".join(PROFILE_LABELS[p].replace(" tier", "") for p in c.profiles if p in r.profiles)
                rows.append((profiles, r.severity, f"`{r.focusNode}`", f"`{r.resultPath}`",
                             f"`sh:{r.component}ConstraintComponent`", r.explanation))
            L.append("SHACL validation must report exactly these results (and nothing else):")
            L.append("")
            L += _table(["Shapes", "Severity", "Focus node", "Property", "Constraint", "Why"], rows)
            L.append("")
            if c.category == "invalid" and len(f.shacl) > 1:
                L += [f"This is one problem: SHACL reports it as {len(f.shacl)} results, one per missing or bad property.", ""]
            if any(r.profiles == ("sff",) for r in f.shacl) and all(r.profiles == ("sff",) for r in f.shacl):
                L += ["Basic tier validation passes: these properties are only checked by the SFF shapes.", ""]
        else:
            L += ["Passes Basic tier and SFF SHACL validation with no results.", ""]
        if f.dq:
            L.append("The data-quality checks must report exactly:")
            L.append("")
            L += _table(["Code", "Node", "Property", "Why"],
                        [(f"`{d.code}`", f"`{d.focusNode}`", f"`{d.resultPath}`", d.explanation) for d in f.dq])
            L.append("")

    if c.importer:
        L += ["## What an importer should do", "", c.importer, ""]

    first = c.files[0].name
    extra = "".join(f" --profile {p}" for p in c.profiles) if set(c.profiles) - {"basic", "sff"} else ""
    L += ["## Check it yourself", "", "```sh",
          f"python -m cidsconformance validate capsules/{c.category}/{c.id}/{first}{extra}"]
    if c.category != "invalid":
        L.append(f"python -m cidsconformance dq capsules/{c.category}/{c.id}/{first}")
    if c.category == "valid":
        L.append(f"python -m cidsconformance compare capsules/{c.category}/{c.id}/{first} your-export.jsonld")
    L += ["```", ""]
    return "\n".join(L)


def render_index(capsules: list[Capsule]) -> dict[str, str]:
    L = ["# Test capsules", "",
         "Generated by `python -m cidsconformance build` from `cidsconformance/generator/catalog.py`. "
         "Don't edit these files by hand.", ""]
    for cat in ("valid", "invalid", "data-quality"):
        L += [f"## {CATEGORY_LABEL[cat]}", ""]
        rows = [(f"[{c.id}]({cat}/{c.id}/README.md)", c.title, c.source) for c in capsules if c.category == cat]
        L += _table(["Capsule", "What it is", "Based on"], rows) + [""]
    index = [{"id": c.id, "category": c.category, "title": c.title,
              "path": f"{c.category}/{c.id}", "files": [f.name for f in c.files]} for c in capsules]
    return {"README.md": "\n".join(L), "index.json": _json(index)}


def _import_files(c: Capsule) -> str:
    if c.id.startswith("V06"):
        return "`part-1-up-to-2024.jsonld`, then `part-2-2025.jsonld`"
    return "`capsule.jsonld` (or `capsule.ttl`)"


def render_results_template(capsules: list[Capsule]) -> dict[str, str]:
    """A results sheet for vendors, as Markdown and CSV, listing every capsule."""
    valid = [c for c in capsules if c.category == "valid"]
    invalid = [c for c in capsules if c.category == "invalid"]
    dq = [c for c in capsules if c.category == "data-quality"]
    L = ["# Vendor results template", "",
         "Copy this file, fill it in, and send it back with the `compare --json` output for every FAIL. "
         "The same table is in [vendor-results-template.csv](vendor-results-template.csv) for spreadsheets. "
         "[SUCCESS_CRITERIA.md](../SUCCESS_CRITERIA.md) says what counts as passing.", "",
         "Generated by `python -m cidsconformance build`.", "",
         "| | |", "|---|---|",
         "| Product and version | |", "| Suite version (git tag or commit) | |", "| Date tested | |", "| Tested by | |", "",
         "## Valid capsules", "",
         "Import, export straight away, then run `compare` and `validate` on the export. "
         "`compare --strict` and the tier shapes (V10: `--profile essential`; V11: `--profile essential --profile full`) are recommended, not required.", ""]
    L += _table(["Capsule", "Import", "Imported OK? (yes/no)", "`compare` (PASS/FAIL)", "`compare --strict` (recommended)",
                 "`validate` Basic + SFF (PASS/FAIL)", "Tier shapes (recommended)", "Notes"],
                [(c.id, _import_files(c), "", "", "", "", "" if set(c.profiles) - {"basic", "sff"} else "n/a", "")
                 for c in valid]) + [""]
    L += ["For V06, compare the export after both imports with `expected-after-both-parts.jsonld`.", "",
          "## Broken capsules", "",
          "Import each one. Record whether the product rejected it, or imported it and showed the user the problem. "
          "Importing silently, or quietly fixing the data, fails.", ""]
    L += _table(["Capsule", "The problem", "Result (rejected / imported with a warning / imported silently)", "Notes"],
                [(c.id, c.title, "", "") for c in invalid]) + [""]
    L += ["## Data-quality capsules", "",
          "Import, export straight away, and run `compare`: these must come back unchanged. "
          "Warning the user about the finding is recommended.", ""]
    L += _table(["Capsule", "The finding", "Imported OK? (yes/no)", "`compare` (PASS/FAIL)", "Warned the user? (recommended)", "Notes"],
                [(c.id, c.title, "", "", "", "") for c in dq]) + [""]

    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["capsule", "category", "imported_ok", "compare", "compare_strict", "validate_basic_sff",
                "tier_shapes", "broken_capsule_result", "dq_warning", "notes"])
    for c in capsules:
        w.writerow([c.id, c.category] + [""] * 8)
    return {"vendor-results-template.md": "\n".join(L), "vendor-results-template.csv": buf.getvalue()}


def render_examples() -> dict[str, str]:
    files = {name: _json(builder()) for name, (_imp, builder, _res, _why) in EXAMPLES.items()}
    L = ["# Round-trip examples", "",
         "Example exports that show what `compare` reports. Each file is a valid capsule from `capsules/valid/` "
         "after a (simulated) import and export. Generated by `python -m cidsconformance build`.", ""]
    rows = []
    for name, (imported, _builder, result, why) in EXAMPLES.items():
        rows.append((f"`{name}`", why, result))
    L += _table(["Export", "What happened", "Expected result"], rows) + [""]
    L += ["Try them:", "", "```sh"]
    for name, (imported, *_rest) in EXAMPLES.items():
        L.append(f"python -m cidsconformance compare {imported} examples/round-trip/{name}")
    L += ["```", ""]
    files["README.md"] = "\n".join(L)
    return files


def build(check: bool = False, out_dir: Path = CAPSULES_DIR, examples_dir: Path = EXAMPLES_DIR) -> list[str]:
    """Write every capsule and example. With check=True, write nothing and
    return the files that are missing or out of date."""
    capsules = all_capsules()
    wanted: dict[Path, str] = {}
    for c in capsules:
        for rel, content in render_files(c).items():
            wanted[out_dir / c.category / c.id / rel] = content
    for rel, content in render_index(capsules).items():
        wanted[out_dir / rel] = content
    for rel, content in render_examples().items():
        wanted[examples_dir / rel] = content
    for rel, content in render_results_template(capsules).items():
        wanted[DOCS_DIR / rel] = content

    problems = []
    for path, content in wanted.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            problems.append(str(path.relative_to(REPO_ROOT)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

    # Files on disk that the generator no longer produces.
    for root in (out_dir, examples_dir):
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and path not in wanted:
                    problems.append(f"{path.relative_to(REPO_ROOT)} (not generated)")
    return problems
