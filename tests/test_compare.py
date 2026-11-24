"""The round-trip comparison catches the failures it is meant to catch, and
nothing else."""

from collections import Counter
from pathlib import Path

import pytest
from rdflib import Literal, URIRef

from cidsconformance.compare import compare_graphs
from cidsconformance.generator.examples import EXAMPLES
from cidsconformance.load import load_graph

ROOT = Path(__file__).resolve().parent.parent
VALID = sorted((ROOT / "capsules" / "valid").glob("*/*.jsonld"))
EXAMPLES_DIR = ROOT / "examples" / "round-trip"


def kinds(report):
    return Counter(d.kind for d in report.differences)


@pytest.mark.parametrize("path", VALID, ids=[f"{p.parent.name}/{p.name}" for p in VALID])
def test_jsonld_and_turtle_copies_compare_equal(path):
    report = compare_graphs(load_graph(path), load_graph(path.with_suffix(".ttl")), strict=True)
    assert report.passed and not report.differences, report.to_text()


@pytest.mark.parametrize(
    "name,expected_kinds",
    [
        ("V01-export-good.jsonld", {}),
        ("V01-export-duplicated-indicator.jsonld", {"DUPLICATE_NODE": 2}),
        ("V01-export-lost-data.jsonld",
         {"IRI_CHANGED": 1, "MISSING_NODE": 1, "MISSING_TRIPLE": 2, "VALUE_CHANGED": 1}),
        ("V04-export-hascomment-clash.jsonld", {"PREDICATE_CHANGED": 2}),
    ],
)
def test_examples(name, expected_kinds):
    imported, _builder, result, _why = EXAMPLES[name]
    report = compare_graphs(load_graph(ROOT / imported), load_graph(EXAMPLES_DIR / name))
    assert dict(kinds(report)) == expected_kinds, report.to_text()
    assert report.passed == (result == "PASS")


def test_duplicate_report_names_the_copies():
    imported, *_ = EXAMPLES["V01-export-duplicated-indicator.jsonld"]
    report = compare_graphs(load_graph(ROOT / imported),
                            load_graph(EXAMPLES_DIR / "V01-export-duplicated-indicator.jsonld"))
    copies = sorted(d.exported for d in report.differences if d.kind == "DUPLICATE_NODE")
    assert copies == [
        "https://northwind-food.example/Indicator/TonnesFoodRecovered-2/",
        "https://northwind-food.example/Indicator/TonnesFoodRecovered-3/",
    ]


def _v03():
    return load_graph(ROOT / "capsules/valid/V03-literal-fidelity/capsule.jsonld")


def test_reformatted_datetime_passes_by_default_but_not_in_strict_mode():
    imported = _v03()
    exported = _v03()
    old = next(o for o in exported.objects() if isinstance(o, Literal) and str(o) == "2023-01-01T05:00:00Z")
    for s, p, _ in list(exported.triples((None, None, old))):
        exported.remove((s, p, old))
        exported.add((s, p, Literal("2023-01-01T00:00:00-05:00", datatype=old.datatype)))
    lenient = compare_graphs(imported, exported)
    assert lenient.passed and kinds(lenient) == {"LITERAL_REFORMATTED": len(list(imported.triples((None, None, old))))}
    assert not compare_graphs(imported, exported, strict=True).passed


def test_numbers_are_compared_as_text():
    imported = _v03()
    exported = _v03()
    old = Literal("27.50")
    for s, p, _ in list(exported.triples((None, None, old))):
        exported.remove((s, p, old))
        exported.add((s, p, Literal("27.5")))
    report = compare_graphs(imported, exported)
    assert not report.passed and kinds(report) == {"VALUE_CHANGED": 1}


def test_extra_triples_fail_unless_allowed():
    imported = _v03()
    exported = _v03()
    exported.add((URIRef("https://ruisseau-vert.example/Organization/RuisseauVert/"),
                  URIRef("https://vendor.example/importedAt"), Literal("2026-11-18")))
    assert not compare_graphs(imported, exported).passed
    assert compare_graphs(imported, exported, allow_extra=True).passed
    assert compare_graphs(imported, exported, ignore_predicates=("https://vendor.example/importedAt",)).passed


def test_incremental_import_expected_file_is_the_union_of_both_parts():
    d = ROOT / "capsules/valid/V06-portfolio-incremental-import"
    union = load_graph(d / "part-1-up-to-2024.jsonld") + load_graph(d / "part-2-2025.jsonld")
    report = compare_graphs(load_graph(d / "expected-after-both-parts.jsonld"), union, strict=True)
    assert report.passed and not report.differences, report.to_text()
