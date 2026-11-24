"""Helpers for writing CIDS/SFF nodes in the same JSON-LD style as the
Airtable/Excel CIDS exports: a top-level array of nodes, each carrying the
CIDS and SFF contexts."""

from __future__ import annotations

import copy
from functools import lru_cache

from rdflib import Namespace, URIRef

from ..reference import codelists_graph

CONTEXT = [
    "https://ontology.commonapproach.org/contexts/cidsContext.jsonld",
    "https://ontology.commonapproach.org/contexts/sffContext.jsonld",
]

CIDS_NS = "https://ontology.commonapproach.org/cids#"
CODELIST = "https://codelist.commonapproach.org/"
CRA = CODELIST + "CanadianCorporateRegistries#cra"

UNIT = {name: CIDS_NS + name for name in (
    "tonne", "countUnit", "percentUnit", "scoreUnit", "cad", "megawattHour",
    "dayUnit", "kilogram", "unspecifiedUnit",
)}

ORG = Namespace("http://ontology.eil.utoronto.ca/tove/organization#")
CIDS = Namespace(CIDS_NS)


def node(type_, id_, **props) -> dict:
    """One JSON-LD node. Keys with a colon (e.g. ``cids:hasComment``) can be
    passed through ``props`` by unpacking a dict."""
    out = {"@context": list(CONTEXT), "@type": type_, "@id": id_}
    out.update({k: v for k, v in props.items() if v is not None})
    return out


def measure(value: str, unit: str | None = None) -> dict:
    m = {"@type": "i72:Measure", "hasNumericalValue": value}
    if unit:
        m["unit_of_measure"] = unit
    return m


@lru_cache(maxsize=None)
def _code_label(iri: str) -> tuple[str, str | None]:
    g = codelists_graph()
    name = g.value(URIRef(iri), ORG.hasName)
    if name is None:
        raise KeyError(f"{iri} is not in the pinned codelists")
    desc = g.value(URIRef(iri), CIDS.hasDescription)
    return str(name), (str(desc) if desc is not None else None)


def sdg_theme(n: int) -> dict:
    """A Theme node for an SDG, using the same name and description as the
    SDGImpacts codelist so the capsule doesn't contradict it."""
    iri = f"https://metadata.un.org/sdg/{n}"
    name, desc = _code_label(iri)
    return node("cids:Theme", iri, hasName=name, hasDescription=desc)


def code_characteristic(iri: str) -> dict:
    """A cids:Characteristic node for a PopulationServed / EDG code.

    SFF's primaryPopulationServed and forEDG must point at a
    cids:Characteristic. The codelists type these codes as
    cids:PopulationServed / cids:EquityDeservingGroup, so the exports declare
    them as Characteristics too (same convention as the Airtable exports)."""
    name, _ = _code_label(iri)
    return node("cids:Characteristic", iri, hasName=name)


def population(code: str) -> str:
    return f"{CODELIST}PopulationServed#{code}"


def edg(code: str) -> str:
    return f"{CODELIST}EquityDeservingGroupsESDC#{code}"


def sector(name: str) -> str:
    return f"{CODELIST}IRISImpactCategory#{name}"


def province(code: str) -> str:
    return f"{CODELIST}ProvinceTerritory#{code}"


def locality(code: str) -> str:
    return f"{CODELIST}LocalityStatsCan#{code}"


def org_type(code: str) -> str:
    return f"{CODELIST}OrgTypeGOC#{code}"


def funding_state(code: str) -> str:
    return f"{CODELIST}FundingState#{code}"


def annual(year: int, tz: str = "-05:00") -> tuple[str, str]:
    return (f"{year}-01-01T00:00:00{tz}", f"{year}-12-31T23:59:59{tz}")


def by_id(nodes: list[dict]) -> dict[str, dict]:
    return {n["@id"]: n for n in nodes}


def clone(nodes: list[dict]) -> list[dict]:
    return copy.deepcopy(nodes)


def find(nodes: list[dict], id_: str) -> dict:
    for n in nodes:
        if n["@id"] == id_:
            return n
    raise KeyError(id_)


def remove(nodes: list[dict], id_: str) -> list[dict]:
    return [n for n in nodes if n["@id"] != id_]
