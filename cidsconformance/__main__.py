"""Command-line interface. Run ``python -m cidsconformance --help``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path


def _quiet():
    # rdflib logs a warning for every ill-typed literal ("Invalid date" ...).
    # The broken capsules have those on purpose; the results say what's wrong.
    logging.getLogger("rdflib").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")


def cmd_validate(args) -> int:
    from .load import load_graph
    from .reference import DEFAULT_PROFILES, PROFILE_LABELS, SHAPES
    from .shacl import validate

    g = load_graph(args.file)
    chosen = args.profile or list(DEFAULT_PROFILES)
    profiles = list(SHAPES) if "all" in chosen else list(dict.fromkeys(chosen))
    out, failed = {}, False
    for p in profiles:
        results = validate(g, p, include_codelist_results=args.include_codelist_results)
        out[p] = [r.to_dict() for r in results]
        failed |= any(r.severity == "Violation" for r in results)
        if not args.json:
            label = PROFILE_LABELS[p]
            counts = {s: sum(r.severity == s for r in results) for s in ("Violation", "Warning", "Info")}
            print(f"{label}: {counts['Violation']} violation(s), {counts['Warning']} warning(s), {counts['Info']} info")
            for r in results:
                print(f"  [{r.severity}] {r.focusNode}")
                print(f"      {r.resultPath}  {r.sourceConstraintComponent}" + (f"  value: {r.value}" if r.value else ""))
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif not failed:
        print("PASS: no SHACL violations")
    return 1 if failed else 0


def cmd_dq(args) -> int:
    from .dq import run_checks
    from .load import load_graph

    findings = run_checks(load_graph(args.file))
    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2, ensure_ascii=False))
    else:
        if not findings:
            print("No data-quality findings.")
        for f in findings:
            print(f"[{f.code}] {f.focusNode}\n    {f.resultPath}: {f.message}")
    return 1 if (findings and args.fail_on_findings) else 0


def cmd_compare(args) -> int:
    from .compare import compare_graphs
    from .load import load_graph

    report = compare_graphs(
        load_graph(args.imported), load_graph(args.exported),
        strict=args.strict, allow_extra=args.allow_extra,
        ignore_predicates=tuple(args.ignore_predicate or ()),
    )
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) if args.json else report.to_text())
    return 0 if report.passed else 1


def cmd_suite(args) -> int:
    from .suite import run_suite

    results = run_suite(args.only)
    bad = [r for r in results if not r.ok]
    if args.json:
        print(json.dumps([{"capsule": r.capsule, "file": r.file, "ok": r.ok, "problems": r.problems}
                          for r in results], indent=2))
    else:
        for r in results:
            print(f"{'ok  ' if r.ok else 'FAIL'}  {r.capsule}/{r.file}")
            for p in r.problems:
                print(f"        {p}")
        print(f"\n{len(results) - len(bad)} of {len(results)} capsule files behave as expected.")
    return 1 if bad else 0


def cmd_build(args) -> int:
    from .build import build

    problems = build(check=args.check)
    if args.check:
        if problems:
            print("Capsules are out of date. Run `python -m cidsconformance build`:")
            for p in problems:
                print(f"  {p}")
            return 1
        print("Capsules are up to date.")
        return 0
    print(f"Wrote {len(problems)} file(s)." if problems else "Nothing to do: capsules are up to date.")
    for p in problems:
        print(f"  {p}")
    return 0


def cmd_to_turtle(args) -> int:
    from .build import to_turtle
    from .load import load_graph

    sys.stdout.write(to_turtle(load_graph(args.file)))
    return 0


def cmd_refresh_reference(args) -> int:
    from .refresh import refresh

    for line in refresh(Path(args.dest) if args.dest else None):
        print(line)
    return 0


def main(argv=None) -> int:
    _quiet()
    p = argparse.ArgumentParser(prog="python -m cidsconformance", description="CIDS conformance test tools.")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="SHACL-validate a capsule (Basic tier and SFF by default)")
    v.add_argument("file")
    v.add_argument("--profile", action="append", choices=["basic", "sff", "essential", "full", "all"],
                   help="shapes to validate against (repeatable; default: basic and sff). "
                        "Essential and Full tier shapes have known bugs that are corrected when loaded: "
                        "see reference/SOURCES.md")
    v.add_argument("--include-codelist-results", action="store_true",
                   help="also show results on codelist nodes (hidden by default, like CIDS-validate.sh)")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=cmd_validate)

    d = sub.add_parser("dq", help="run the data-quality checks on a capsule")
    d.add_argument("file")
    d.add_argument("--json", action="store_true")
    d.add_argument("--fail-on-findings", action="store_true", help="exit 1 if anything is found")
    d.set_defaults(func=cmd_dq)

    c = sub.add_parser("compare", help="compare an exported capsule with the one that was imported")
    c.add_argument("imported", help="the capsule you imported (e.g. a file from capsules/valid/)")
    c.add_argument("exported", help="what your software exported (.jsonld, .json or .ttl)")
    c.add_argument("--strict", action="store_true",
                   help="also fail on literals that were reformatted but keep the same value (e.g. time zones)")
    c.add_argument("--allow-extra", action="store_true",
                   help="don't fail on triples the export added (they are still listed)")
    c.add_argument("--ignore-predicate", action="append", metavar="IRI",
                   help="leave this property out of the comparison (repeatable)")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_compare)

    s = sub.add_parser("suite", help="check every capsule gives its expected results")
    s.add_argument("only", nargs="*", help="only these capsule ids / categories (substring match)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_suite)

    b = sub.add_parser("build", help="regenerate capsules/ from the generator")
    b.add_argument("--check", action="store_true", help="don't write; exit 1 if capsules/ is out of date")
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("to-turtle", help="print a capsule as Turtle")
    t.add_argument("file")
    t.set_defaults(func=cmd_to_turtle)

    r = sub.add_parser("refresh-reference", help="download the latest shapes, contexts and codelists")
    r.add_argument("--dest", help="folder to write to (default: reference/)")
    r.set_defaults(func=cmd_refresh_reference)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
