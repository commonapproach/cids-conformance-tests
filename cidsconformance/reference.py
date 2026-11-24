"""Pinned reference data: SHACL shapes, JSON-LD contexts and codelists.

The files live in ``reference/`` at the repository root. See
``reference/SOURCES.md`` for where each one came from and how to refresh it.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from rdflib import Graph

REPO_ROOT = Path(__file__).resolve().parent.parent

# CIDS_REFERENCE_DIR lets CI (or a vendor) point the tools at a different
# copy of the reference data, e.g. freshly downloaded shapes.
REFERENCE_DIR = Path(os.environ.get("CIDS_REFERENCE_DIR", REPO_ROOT / "reference"))

CONTEXT_URLS = {
    "https://ontology.commonapproach.org/contexts/cidsContext.jsonld": "contexts/cidsContext.jsonld",
    "https://ontology.commonapproach.org/contexts/sffContext.jsonld": "contexts/sffContext.jsonld",
}

SHAPES = {
    "basic": "shacl/cids.basictier.shacl.ttl",
    "sff": "shacl/sff.shacl.ttl",
    "essential": "shacl/cids.essentialtier.shacl.ttl",
    "full": "shacl/cids.fulltier.shacl.ttl",
}

SHAPES_URLS = {
    "basic": "https://ontology.commonapproach.org/validation/shacl/cids.basictier.shacl.ttl",
    "sff": "https://ontology.commonapproach.org/validation/shacl/sff.shacl.ttl",
    "essential": "https://ontology.commonapproach.org/validation/shacl/cids.essentialtier.shacl.ttl",
    "full": "https://ontology.commonapproach.org/validation/shacl/cids.fulltier.shacl.ttl",
}

PROFILE_LABELS = {
    "basic": "Basic tier",
    "sff": "SFF",
    "essential": "Essential tier",
    "full": "Full tier",
}

# What `validate` checks when no profile is given: the ticket's rule is that
# every valid capsule passes Basic tier and SFF.
DEFAULT_PROFILES = ("basic", "sff")

CODELIST_BASE_URL = "https://codelist.commonapproach.org"

# Same list the official CIDS-validate.sh script merges with --codelists.
CODELISTS = [
    "CanadianCorporateRegistries",
    "EquityDeservingGroupsESDC",
    "ESDCSector",
    "FundingState",
    "IRISImpactCategory",
    "IRISImpactTheme",
    "LocalityStatsCan",
    "OrgTypeGOC",
    "PopulationServed",
    "ProvinceTerritory",
    "RallyImpactArea",
    "SDGImpacts",
    "SELI-GLI",
    "UnitsOfMeasureList",
]

# Not published online; copied from the CIDS repo (see SOURCES.md).
EXTRA_REFERENCE_FILES = ["cids-codes-and-orgs.ttl"]


@lru_cache(maxsize=None)
def context_document(url: str) -> dict | None:
    """Return the pinned copy of a known CIDS context, or None if unknown."""
    rel = CONTEXT_URLS.get(url)
    if rel is None:
        return None
    with open(REFERENCE_DIR / rel, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def published_shapes_graph(profile: str) -> Graph:
    """The shapes exactly as published (the pinned file)."""
    if profile not in SHAPES:
        raise ValueError(f"unknown profile {profile!r}; expected one of {sorted(SHAPES)}")
    g = Graph()
    g.parse(REFERENCE_DIR / SHAPES[profile], format="turtle")
    return g


@lru_cache(maxsize=None)
def shapes_graph(profile: str) -> Graph:
    """The shapes used for validation: the published file with the known
    bugs corrected (see ``shape_fixes.py``)."""
    from .shape_fixes import corrected

    g, _ = corrected(published_shapes_graph(profile))
    return g


def shape_corrections(profile: str):
    """What ``shapes_graph`` changed for this profile."""
    from .shape_fixes import corrected

    return corrected(published_shapes_graph(profile))[1]


@lru_cache(maxsize=None)
def codelists_graph() -> Graph:
    """All codelists plus cids-codes-and-orgs.ttl, merged into one graph.

    This mirrors ``CIDS-validate.sh --codelists``: the codelists are merged
    into the data graph so that ``sh:class`` checks on codelist IRIs (sectors,
    provinces, registries, units ...) can see the codes' ``rdf:type``.
    """
    g = Graph()
    for name in CODELISTS:
        g.parse(REFERENCE_DIR / "codelists" / f"{name}.ttl", format="turtle")
    for name in EXTRA_REFERENCE_FILES:
        g.parse(REFERENCE_DIR / "codelists" / name, format="turtle")
    return g
