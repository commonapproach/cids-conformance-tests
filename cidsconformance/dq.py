"""Data-quality (DQ) checks.

These catch problems that SHACL can't express with the current shapes: data
that is valid CIDS but probably wrong (an outlier value, a missing year in a
time series, address fields in the wrong slots, ...).

DQ findings are warnings for the person reviewing the data. They don't make a
capsule invalid. Each check has a stable code (e.g. ``DQ-TIME-SERIES-GAP``)
that test expectations refer to; see ``docs/data-quality-checks.md``.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from rdflib import Graph, Literal, Namespace, RDF, URIRef

from .reference import codelists_graph
from .shacl import describe_node, is_codelist_node

CIDS = Namespace("https://ontology.commonapproach.org/cids#")
SFF = Namespace("https://ontology.commonapproach.org/sff#")
ORG = Namespace("http://ontology.eil.utoronto.ca/tove/organization#")
I72 = Namespace("http://ontology.eil.utoronto.ca/ISO21972/iso21972#")
PROV = Namespace("http://www.w3.org/ns/prov#")

CRA = URIRef("https://codelist.commonapproach.org/CanadianCorporateRegistries#cra")

# Thresholds, documented in docs/data-quality-checks.md.
OUTLIER_FACTOR = 5          # value > 5x (or < 1/5 of) the median of the other values
OUTLIER_MIN_POINTS = 4      # need at least this many values in the series
GAP_TOLERANCE = 0.5         # a gap longer than half the usual period is reported

NUMBER_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
BN15_RE = re.compile(r"^\d{9}[A-Z]{2}\d{4}$")
CA_POSTAL_RE = re.compile(r"^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$")
US_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
COUNTRY_WORDS = {"canada", "ca", "can", "united states", "usa", "us", "united states of america"}
CANADA = {"canada", "ca", "can"}


@dataclass(frozen=True, order=True)
class DQFinding:
    code: str
    focusNode: str
    resultPath: str
    message: str = ""

    def key(self) -> tuple:
        return (self.code, self.focusNode, self.resultPath)

    def to_dict(self) -> dict:
        return asdict(self)


def _str(g: Graph, s, p) -> str | None:
    v = g.value(s, p)
    return None if v is None else str(v)


def _reporting_orgs(g: Graph) -> list:
    """Organizations that report data in this capsule (not funders/standards bodies)."""
    orgs = set()
    for s in g.subjects(RDF.type, CIDS.Organization):
        if is_codelist_node(s):
            continue
        if (s, CIDS.hasIndicator, None) in g or (s, CIDS.hasOutcome, None) in g:
            orgs.add(s)
    for profile in g.subjects(RDF.type, SFF.OrganizationProfile):
        org = g.value(profile, CIDS.forOrganization)
        if org is not None:
            orgs.add(org)
    return sorted(orgs, key=str)


def _parse_dt(lit) -> datetime | None:
    if lit is None:
        return None
    try:
        return datetime.fromisoformat(str(lit).replace("Z", "+00:00"))
    except ValueError:
        return None


def _number(text: str | None) -> Decimal | None:
    if text is None or not NUMBER_RE.match(text.strip()):
        return None
    try:
        return Decimal(text.strip())
    except InvalidOperation:
        return None


def _reports_by_indicator(g: Graph) -> dict:
    by_ind: dict = {}
    for ind in g.subjects(RDF.type, CIDS.Indicator):
        by_ind.setdefault(ind, set())
        by_ind[ind].update(g.objects(ind, CIDS.hasIndicatorReport))
    for rep in g.subjects(RDF.type, CIDS.IndicatorReport):
        ind = g.value(rep, CIDS.forIndicator)
        if ind is not None:
            by_ind.setdefault(ind, set()).add(rep)
    return by_ind


def check_missing_address(g: Graph):
    for org in _reporting_orgs(g):
        if g.value(org, CIDS.hasAddress) is None:
            yield DQFinding("DQ-MISSING-ADDRESS", describe_node(g, org), "cids:hasAddress",
                            "Reporting organization has no address.")


def check_missing_org_id(g: Graph):
    # Only for organizations with an SFF OrganizationProfile: Basic tier
    # capsules commonly have no OrganizationID at all.
    sff_orgs = {g.value(p, CIDS.forOrganization) for p in g.subjects(RDF.type, SFF.OrganizationProfile)}
    for org in _reporting_orgs(g):
        if org in sff_orgs and g.value(org, ORG.hasID) is None:
            yield DQFinding("DQ-MISSING-ORG-ID", describe_node(g, org), "org:hasID",
                            "Reporting organization has no OrganizationID (e.g. business number).")


def check_missing_contact(g: Graph):
    for profile in sorted(g.subjects(RDF.type, SFF.OrganizationProfile), key=str):
        if g.value(profile, SFF.hasPrimaryContact) is None:
            yield DQFinding("DQ-MISSING-CONTACT", describe_node(g, profile), "sff:hasPrimaryContact",
                            "Organization profile has no primary contact.")


def check_indicator_without_reports(g: Graph):
    for ind, reps in sorted(_reports_by_indicator(g).items(), key=lambda kv: str(kv[0])):
        if (ind, RDF.type, CIDS.Indicator) in g and not reps:
            yield DQFinding("DQ-INDICATOR-NO-REPORTS", describe_node(g, ind), "cids:hasIndicatorReport",
                            "Indicator has no indicator reports.")


def check_identifier_format(g: Graph):
    for oid in sorted(g.subjects(RDF.type, ORG.OrganizationID), key=str):
        ident = _str(g, oid, ORG.hasIdentifier)
        if ident is None:
            continue  # missing identifier is a SHACL violation, not a DQ finding
        if re.search(r"\s", ident):
            yield DQFinding("DQ-IDENTIFIER-FORMAT", describe_node(g, oid), "org:hasIdentifier",
                            f"Identifier {ident!r} contains whitespace.")
        elif g.value(oid, ORG.issuedBy) == CRA and not BN15_RE.match(ident):
            yield DQFinding("DQ-IDENTIFIER-FORMAT", describe_node(g, oid), "org:hasIdentifier",
                            f"Identifier {ident!r} is not a 15-character CRA business number (123456789RC0001).")


def check_numeric_values(g: Graph):
    for measure, value in sorted(g.subject_objects(I72.hasNumericalValue), key=lambda x: str(x[1])):
        if _number(str(value)) is None:
            yield DQFinding("DQ-NON-NUMERIC-VALUE", describe_node(g, measure), "i72:hasNumericalValue",
                            f"Value {str(value)!r} is empty or not a number.")


def _series(g: Graph, reports) -> list:
    rows = []
    for rep in reports:
        start = _parse_dt(g.value(rep, PROV.startedAtTime))
        end = _parse_dt(g.value(rep, PROV.endedAtTime))
        measure = g.value(rep, I72.value)
        num = _number(_str(g, measure, I72.hasNumericalValue)) if measure is not None else None
        rows.append((start, end, num, rep))
    return rows


def check_outliers(g: Graph):
    for ind, reps in sorted(_reports_by_indicator(g).items(), key=lambda kv: str(kv[0])):
        rows = [r for r in _series(g, reps) if r[2] is not None]
        if len(rows) < OUTLIER_MIN_POINTS:
            continue
        for start, end, num, rep in rows:
            others = [r[2] for r in rows if r[3] != rep]
            median = statistics.median(others)
            if median <= 0:
                continue
            if num > median * OUTLIER_FACTOR or num < median / OUTLIER_FACTOR:
                measure = g.value(rep, I72.value)
                yield DQFinding("DQ-OUTLIER", describe_node(g, measure), "i72:hasNumericalValue",
                                f"Value {num} is far from the median ({median}) of the other reports for this indicator.")


def check_time_series_gaps(g: Graph):
    for ind, reps in sorted(_reports_by_indicator(g).items(), key=lambda kv: str(kv[0])):
        rows = sorted((r for r in _series(g, reps) if r[0] and r[1]), key=lambda r: r[0])
        if len(rows) < 2:
            continue
        period = statistics.median((r[1] - r[0]).total_seconds() for r in rows)
        for prev, nxt in zip(rows, rows[1:]):
            gap = (nxt[0] - prev[1]).total_seconds()
            if gap > period * GAP_TOLERANCE:
                yield DQFinding("DQ-TIME-SERIES-GAP", describe_node(g, ind), "cids:hasIndicatorReport",
                                f"No report covers {prev[1].date()} to {nxt[0].date()}.")


def check_address_fields(g: Graph):
    for addr in sorted(g.subjects(RDF.type, CIDS.Address), key=str):
        postal = (_str(g, addr, CIDS.postalCode) or "").strip()
        country = (_str(g, addr, CIDS.addressCountry) or "").strip()
        if postal.lower() in COUNTRY_WORDS or CA_POSTAL_RE.match(country) or US_ZIP_RE.match(country):
            yield DQFinding("DQ-ADDRESS-FIELDS-SWAPPED", describe_node(g, addr), "cids:postalCode",
                            f"postalCode {postal!r} and addressCountry {country!r} look swapped.")
        elif country.lower() in CANADA and postal and not CA_POSTAL_RE.match(postal):
            yield DQFinding("DQ-POSTAL-CODE-FORMAT", describe_node(g, addr), "cids:postalCode",
                            f"{postal!r} is not a Canadian postal code (A1A 1A1).")


def check_units(g: Graph):
    known = set(codelists_graph().subjects(RDF.type, None))
    known |= {s for s, o in g.subject_objects(RDF.type) if str(o).startswith(str(I72))}
    for node, unit in sorted(g.subject_objects(I72.unit_of_measure), key=lambda x: (str(x[0]), str(x[1]))):
        if isinstance(unit, Literal) or unit not in known:
            yield DQFinding("DQ-UNKNOWN-UNIT", describe_node(g, node), "i72:unit_of_measure",
                            f"Unit {str(unit)!r} is not in the CIDS units list and is not defined in the capsule.")


CHECKS = [
    check_missing_address,
    check_missing_org_id,
    check_missing_contact,
    check_indicator_without_reports,
    check_identifier_format,
    check_numeric_values,
    check_outliers,
    check_time_series_gaps,
    check_address_fields,
    check_units,
]


def run_checks(g: Graph) -> list[DQFinding]:
    findings = set()
    for check in CHECKS:
        findings.update(check(g))
    return sorted(findings)
