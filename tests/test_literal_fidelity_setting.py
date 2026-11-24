"""pyshacl turns rdflib's literal normalization back on after it runs.
Make sure validation doesn't leave it that way."""

from pathlib import Path

import rdflib

from cidsconformance.load import load_graph
from cidsconformance.shacl import validate

CAPSULE = Path(__file__).resolve().parent.parent / "capsules/valid/V03-literal-fidelity/capsule.jsonld"


def test_validation_does_not_switch_on_literal_normalization():
    validate(load_graph(CAPSULE), "basic")
    assert rdflib.NORMALIZE_LITERALS is False
    lexical = {str(o) for o in load_graph(CAPSULE).objects() if isinstance(o, rdflib.Literal)}
    assert "2023-01-01T05:00:00Z" in lexical
    assert "2023-12-31T23:59:59.999-05:00" in lexical
