"""SHACL validation against the CIDS Basic tier and SFF shapes.

Validation mirrors the official ``CIDS-validate.sh --codelists`` script in the
CIDS repo: the codelists are merged into the data graph, no inference is run,
and results whose focus node only appears in the codelists are dropped.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import rdflib
from pyshacl import validate as pyshacl_validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef

from .reference import codelists_graph, shapes_graph

SH = Namespace("http://www.w3.org/ns/shacl#")

PREFIXES = {
    "cids": "https://ontology.commonapproach.org/cids#",
    "sff": "https://ontology.commonapproach.org/sff#",
    "org": "http://ontology.eil.utoronto.ca/tove/organization#",
    "i72": "http://ontology.eil.utoronto.ca/ISO21972/iso21972#",
    "prov": "http://www.w3.org/ns/prov#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "ic": "http://ontology.eil.utoronto.ca/tove/icontact#",
    "sh": "http://www.w3.org/ns/shacl#",
    "csh": "https://ontology.commonapproach.org/cids/shacl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "schema": "http://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


def qname(term) -> str:
    """Shorten an IRI with the CIDS prefixes; leave other IRIs as they are."""
    if term is None:
        return ""
    s = str(term)
    best = None
    for prefix, ns in PREFIXES.items():
        if s.startswith(ns) and (best is None or len(ns) > len(PREFIXES[best])):
            best = prefix
    return f"{best}:{s[len(PREFIXES[best]):]}" if best else s


def describe_node(g: Graph, node, _depth: int = 0) -> str:
    """A stable, human-readable name for a node.

    IRIs are printed as-is. Blank nodes (e.g. the i72:Measure behind an
    IndicatorReport's value) are named by the triple that points at them:
    ``<report IRI> / i72:value``.
    """
    if isinstance(node, URIRef):
        return str(node)
    if isinstance(node, Literal):
        return f'"{node}"'
    if isinstance(node, BNode) and _depth < 3:
        refs = sorted(g.subject_predicates(node), key=lambda sp: (str(sp[0]), str(sp[1])))
        if refs:
            subj, pred = refs[0]
            return f"{describe_node(g, subj, _depth + 1)} / {qname(pred)}"
    return "_:blank"


@dataclass(frozen=True, order=True)
class ShaclResult:
    severity: str           # Violation | Warning | Info
    focusNode: str
    resultPath: str
    sourceConstraintComponent: str
    sourceShape: str = ""
    value: str = ""
    message: str = ""

    def key(self) -> tuple:
        """The fields a test expectation is matched on."""
        return (self.severity, self.focusNode, self.resultPath, self.sourceConstraintComponent)

    def to_dict(self) -> dict:
        return asdict(self)


# Same patterns as is_codelist_node() in the official summarize_shacl_violations.py:
# results on these nodes come from the codelists, not from the capsule.
CODELIST_DOMAINS = ("codelist.commonapproach.org", "metadata.un.org")


def is_codelist_node(node) -> bool:
    return isinstance(node, URIRef) and any(d in str(node) for d in CODELIST_DOMAINS)


def validate(capsule: Graph, profile: str, include_codelist_results: bool = False) -> list[ShaclResult]:
    """Validate a capsule graph against one profile ("basic" or "sff")."""
    data = Graph()
    for triple in codelists_graph():
        data.add(triple)
    for triple in capsule:
        data.add(triple)

    # pyshacl switches rdflib.NORMALIZE_LITERALS back on when it finishes,
    # which would make later parsing rewrite literals. Put it back.
    normalize = rdflib.NORMALIZE_LITERALS
    try:
        _conforms, report, _text = pyshacl_validate(
            data,
            shacl_graph=shapes_graph(profile),
            inference="none",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
            inplace=True,
        )
    finally:
        rdflib.NORMALIZE_LITERALS = normalize

    capsule_subjects = set(capsule.subjects())
    results = []
    for r in report.subjects(RDF.type, SH.ValidationResult):
        focus = report.value(r, SH.focusNode)
        if not include_codelist_results and (focus not in capsule_subjects or is_codelist_node(focus)):
            continue
        value = report.value(r, SH.value)
        results.append(
            ShaclResult(
                severity=qname(report.value(r, SH.resultSeverity)).replace("sh:", ""),
                focusNode=describe_node(capsule if focus in capsule_subjects else data, focus),
                resultPath=qname(report.value(r, SH.resultPath)),
                sourceConstraintComponent=qname(report.value(r, SH.sourceConstraintComponent)),
                sourceShape=qname(report.value(r, SH.sourceShape)),
                value=describe_node(data, value) if value is not None else "",
                message=str(report.value(r, SH.resultMessage) or ""),
            )
        )
    return sorted(set(results))


def violations(results: list[ShaclResult]) -> list[ShaclResult]:
    return [r for r in results if r.severity == "Violation"]
