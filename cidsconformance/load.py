"""Load capsules (JSON-LD or Turtle) into rdflib graphs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from rdflib import XSD, Graph, Literal

from .reference import context_document

# Relative IRIs (e.g. a bare "Days" in an @id-typed field) resolve against
# this base, so that the same file always parses to the same graph no matter
# where it sits on disk.
DEFAULT_BASE = "urn:cids-conformance:relative:"

JSONLD_SUFFIXES = {".json", ".jsonld"}
TURTLE_SUFFIXES = {".ttl"}
OTHER_FORMATS = {".nt": "nt", ".nq": "nquads", ".rdf": "xml", ".xml": "xml", ".trig": "trig"}


def _inline_contexts(node: Any) -> Any:
    """Replace references to the CIDS/SFF context URLs with the pinned copies.

    Unknown context URLs are left alone (rdflib will fetch them).
    """
    if isinstance(node, list):
        return [_inline_contexts(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        if key == "@context":
            out[key] = _resolve_context(value)
        else:
            out[key] = _inline_contexts(value)
    return out


def _resolve_context(value: Any) -> Any:
    if isinstance(value, list):
        return [_resolve_context(v) for v in value]
    if isinstance(value, str):
        doc = context_document(value)
        if doc is not None:
            return copy.deepcopy(doc["@context"])
    return value


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _canonical(parsed: Graph) -> Graph:
    """Make literals compare the way RDF 1.1 says they should.

    * ``"x"`` and ``"x"^^xsd:string`` are the same literal in RDF 1.1, but
      rdflib keeps them apart. Typed-string literals become plain ones.
    * rdflib's JSON-LD parser builds typed literals from JSON numbers without
      checking the lexical form, so e.g. -3 typed xsd:nonNegativeInteger is
      not marked ill-typed and SHACL misses it (the Turtle parser catches
      it). Rebuilding each literal from its lexical form makes both agree.
    """
    g = Graph()
    for s, p, o in parsed:
        if isinstance(o, Literal) and o.datatype is not None:
            o = Literal(str(o)) if o.datatype == XSD.string else Literal(str(o), datatype=o.datatype)
        g.add((s, p, o))
    return g


def graph_from_jsonld(data: Any, base: str = DEFAULT_BASE) -> Graph:
    parsed = Graph()
    parsed.parse(data=json.dumps(_inline_contexts(data)), format="json-ld", base=base)
    return _canonical(parsed)


def load_graph(path: str | Path, base: str = DEFAULT_BASE) -> Graph:
    """Parse a capsule file. The format is chosen from the file extension."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in JSONLD_SUFFIXES:
        return graph_from_jsonld(load_json(path), base=base)
    g = Graph()
    if suffix in TURTLE_SUFFIXES:
        g.parse(path, format="turtle", publicID=base)
    elif suffix in OTHER_FORMATS:
        g.parse(path, format=OTHER_FORMATS[suffix], publicID=base)
    else:
        raise ValueError(f"don't know how to read {path.name}: use .jsonld, .json or .ttl")
    return _canonical(g)
