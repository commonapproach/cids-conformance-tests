"""Example "exports" used to show (and test) what ``compare`` reports.

Each one starts from a valid capsule and changes it the way a buggy
import/export cycle would.
"""

from __future__ import annotations

import copy

from .catalog import v01_indicator_multiple_outcomes, v04_uncommon_properties
from .common import CONTEXT

CIDS = "https://ontology.commonapproach.org/cids#"


def _nodes(capsule):
    return copy.deepcopy(capsule.files[0].nodes)


def _as_graph_doc(nodes):
    """Re-shape into a single @graph document with one shared context,
    the way many JSON-LD libraries write their output."""
    body = []
    for n in nodes:
        n = {k: v for k, v in n.items() if k != "@context"}
        body.append(n)
    return {"@context": list(CONTEXT), "@graph": body}


def good_export() -> dict:
    """Same data, different JSON-LD layout: one @graph, nodes in reverse
    order, some properties written as full IRIs. compare must PASS."""
    nodes = list(reversed(_nodes(v01_indicator_multiple_outcomes())))
    for n in nodes:
        if "hasDescription" in n:
            n[CIDS + "hasDescription"] = n.pop("hasDescription")
    return _as_graph_doc(nodes)


def duplicated_indicator_export() -> dict:
    """A known round-trip failure: an Indicator linked to three Outcomes comes back as
    three Indicator nodes, one per Outcome."""
    nodes = _nodes(v01_indicator_multiple_outcomes())
    ind_iri = "https://northwind-food.example/Indicator/TonnesFoodRecovered/"
    ind = next(n for n in nodes if n["@id"] == ind_iri)
    outcomes = ind["forOutcome"]
    ind["forOutcome"] = outcomes[0]
    for k, outcome in enumerate(outcomes[1:], start=2):
        dup = copy.deepcopy(ind)
        dup["@id"] = f"https://northwind-food.example/Indicator/TonnesFoodRecovered-{k}/"
        dup["forOutcome"] = outcome
        nodes.append(dup)
        for n in nodes:
            if n["@id"] == outcome:
                n["hasIndicator"] = [dup["@id"] if x == ind_iri else x for x in n["hasIndicator"]]
            if n["@id"] == "https://northwind-food.example/Organization/Northwind/":
                n["hasIndicator"].append(dup["@id"])
    return _as_graph_doc(nodes)


def lost_data_export() -> dict:
    """An export that re-mints an IRI, drops a property, rewrites a number
    and loses a report."""
    nodes = _nodes(v01_indicator_multiple_outcomes())
    old = "https://northwind-food.example/Outcome/LessFoodWaste/"
    new = "urn:uuid:0d5c9f9e-6a3b-4f1e-9d55-1c2b3a4d5e6f"

    def swap(v):
        if isinstance(v, list):
            return [swap(x) for x in v]
        return new if v == old else v

    lost_report = "https://northwind-food.example/IndicatorReport/MealsProvided/2022"
    out = []
    for n in nodes:
        if n["@id"] == lost_report:
            continue
        n = {k: (v if k == "@context" else swap(v)) for k, v in n.items()}
        if n["@id"] == "https://northwind-food.example/Indicator/MealsProvided/":
            n.pop("hasDescription")
            n["hasIndicatorReport"] = [r for r in n["hasIndicatorReport"] if r != lost_report]
        if n["@id"] == "https://northwind-food.example/IndicatorReport/TonnesFoodRecovered/2023":
            n["value"]["hasNumericalValue"] = "1115.0"
        out.append(n)
    return _as_graph_doc(out)


def hascomment_clash_export() -> dict:
    """V04 written back with the short key "hasComment" while both contexts
    are loaded: the SFF context turns it into sff:hasComment."""
    nodes = _nodes(v04_uncommon_properties())
    for n in nodes:
        if "cids:hasComment" in n:
            n["hasComment"] = n.pop("cids:hasComment")
    return _as_graph_doc(nodes)


EXAMPLES = {
    # file name: (imported capsule, builder, expected outcome, what it shows)
    "V01-export-good.jsonld": (
        "capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld", good_export, "PASS",
        "Same data in a different JSON-LD layout (@graph, reordered nodes, full-IRI keys)."),
    "V01-export-duplicated-indicator.jsonld": (
        "capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld", duplicated_indicator_export, "FAIL",
        "The Indicator linked to three Outcomes came back as three Indicators (DUPLICATE_NODE)."),
    "V01-export-lost-data.jsonld": (
        "capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld", lost_data_export, "FAIL",
        "An Outcome IRI was re-minted, a description dropped, a value rewritten and a report lost."),
    "V04-export-hascomment-clash.jsonld": (
        "capsules/valid/V04-uncommon-properties/capsule.jsonld", hascomment_clash_export, "FAIL",
        "cids:hasComment came back as sff:hasComment (PREDICATE_CHANGED)."),
}
