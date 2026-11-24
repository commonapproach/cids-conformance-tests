"""Every capsule in the suite: what it contains, what it tests, and the
result it must produce.

Expected SHACL results and DQ findings are written by hand here. They are
not copied from validator output: ``python -m cidsconformance suite`` checks
that the real results match these expectations exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import UNIT, clone, find, measure, node, remove, sdg_theme
from .tiers import essential_tier_nodes, full_tier_nodes
from .world import (
    IndicatorSpec, OrgSpec, OutcomeSpec, SDG, annual_series, build_org, maple_hollow,
    merge_nodes, northwind, prairie_spoke, riverbend, tamarack,
)

BOTH = ("basic", "sff")
SFF_ONLY = ("sff",)
ESSENTIAL = ("basic", "sff", "essential")
FULL = ("basic", "sff", "essential", "full")


@dataclass
class Shacl:
    focusNode: str
    resultPath: str
    component: str              # e.g. "MinCount" -> sh:MinCountConstraintComponent
    explanation: str
    profiles: tuple = BOTH
    severity: str = "Violation"

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "focusNode": self.focusNode,
            "resultPath": self.resultPath,
            "sourceConstraintComponent": f"sh:{self.component}ConstraintComponent",
            "explanation": self.explanation,
        }


@dataclass
class DQ:
    code: str
    focusNode: str
    resultPath: str
    explanation: str

    def to_dict(self) -> dict:
        return {"code": self.code, "focusNode": self.focusNode, "resultPath": self.resultPath,
                "explanation": self.explanation}


@dataclass
class CapsuleFile:
    name: str
    nodes: list[dict]
    shacl: list[Shacl] = field(default_factory=list)
    dq: list[DQ] | None = field(default_factory=list)   # None = DQ not checked
    description: str = ""


@dataclass
class Capsule:
    id: str
    category: str               # valid | invalid | data-quality
    title: str
    summary: str
    files: list[CapsuleFile]
    covers: list[str] = field(default_factory=list)     # what it tests, plain language
    roundtrip: list[str] = field(default_factory=list)  # what must come back unchanged
    source: str = ""            # where the scenario came from
    importer: str = ""          # what an importer should do with it
    profiles: tuple = BOTH      # the shapes this capsule is validated against

    def expected(self) -> dict:
        out = {}
        for f in self.files:
            out[f.name] = {
                "shacl": {p: [r.to_dict() for r in f.shacl if p in r.profiles] for p in self.profiles},
                "dq": None if f.dq is None else [d.to_dict() for d in f.dq],
            }
        return out


# Standard round-trip promises that apply to every valid capsule.
GENERAL_ROUNDTRIP = [
    "Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.",
    "Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.",
    "No node is duplicated and no extra nodes are added.",
]


# ==========================================================================
# Valid capsules
# ==========================================================================

def v01_indicator_multiple_outcomes() -> Capsule:
    years = [2022, 2023, 2024, 2025]
    o = northwind(years)
    o.sff = False
    o.outcomes.append(OutcomeSpec(
        "LowerLandfillMethane", "Lower methane emissions from landfills",
        "Less organic waste in landfills means less methane released.", themes=[SDG + "13"]))
    o.sdgs.append(13)
    o.indicators[0].outcomes = ["LessFoodWaste", "ImprovedFoodSecurity", "LowerLandfillMethane"]
    ind = o.indicator("TonnesFoodRecovered")
    return Capsule(
        id="V01-indicator-multiple-outcomes",
        category="valid",
        title="One Indicator linked to several Outcomes",
        summary=("Northwind Food Recovery Society (Basic tier). The Indicator \"Tonnes of food recovered\" "
                 "serves three Outcomes, and the Outcome \"Improved food security\" is measured by two Indicators."),
        source="New. No sample capsule linked an Indicator to more than one Outcome, and duplicating such an Indicator on export is a known round-trip failure.",
        covers=[
            "`cids:forOutcome` with three values on one Indicator, and the matching `cids:hasIndicator` on each Outcome.",
            "An Outcome with two Indicators (many-to-many).",
            "A control Indicator with a single Outcome.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            f"`{ind}` comes back as **one** Indicator node, not one copy per Outcome.",
            "That Indicator keeps all three `forOutcome` links, and each of the three Outcomes keeps its `hasIndicator` link back to it.",
            "Its four IndicatorReports still point at the one Indicator.",
        ],
        files=[CapsuleFile("capsule.jsonld", build_org(o))],
    )


def v02_stable_uris() -> Capsule:
    b = "https://kestrel-arts.example"
    org = "http://legacy.kestrel-arts.example/Organization/1"
    address = f"{b}:8443/address/main"
    oc_community = f"{b}/impact#outcome-community"
    oc_youth = f"{b}//Outcome/YouthArts"
    ind_upper = f"{b}/Indicator/Workshops"
    ind_lower = f"{b}/Indicator/workshops/"
    ind_uuid = "urn:uuid:6f1c2a7e-3b9d-4c55-9a1e-2d7f0b8c4e91"
    ind_tag = "tag:kestrel-arts.example,2026:indicator/volunteer-hours"
    rep_query = f"{b}/data?type=report&id=2024-001"
    rep_pct = f"{b}/r%C3%A9sultats/2024/ateliers"
    rep_space = f"{b}/Indicator%20Report/2024/participants"
    rep_plain = f"{b}/IndicatorReport/volunteer-hours/2024"
    start, end = "2024-01-01T00:00:00-05:00", "2024-12-31T23:59:59-05:00"

    def report(iri, name, ind, value, unit):
        return node("cids:IndicatorReport", iri, hasName=name, value=measure(value, unit),
                    startedAtTime=start, endedAtTime=end, forIndicator=ind, forOrganization=org)

    nodes = [
        node("cids:Organization", org, hasLegalName="Kestrel Community Arts Society",
             hasAddress=[address], hasOutcome=[oc_community, oc_youth],
             hasIndicator=[ind_upper, ind_lower, ind_uuid, ind_tag]),
        node("cids:Address", address, streetAddress="3 Example Mews", addressLocality="Halifax",
             addressRegion="NS", postalCode="B3H 0A6", addressCountry="Canada"),
        sdg_theme(4), sdg_theme(11),
        node("cids:Outcome", oc_community, hasName="Stronger community connections",
             hasDescription="Residents meet and create together.", forTheme=[SDG + "11"],
             forOrganization=org, hasIndicator=[ind_upper, ind_tag]),
        node("cids:Outcome", oc_youth, hasName="Youth arts skills",
             hasDescription="Young people learn an art form.", forTheme=[SDG + "4"],
             forOrganization=org, hasIndicator=[ind_lower, ind_uuid]),
        node("cids:Indicator", ind_upper, hasName="Community workshops held",
             hasDescription="Workshops open to all residents.", unitDescription="Workshops",
             unit_of_measure=UNIT["countUnit"], forOrganization=org, forOutcome=oc_community,
             hasIndicatorReport=[rep_query]),
        node("cids:Indicator", ind_lower, hasName="Youth workshops held",
             hasDescription="Workshops for participants aged 12-18. A different Indicator from .../Indicator/Workshops: IRIs are case-sensitive.",
             unitDescription="Workshops", unit_of_measure=UNIT["countUnit"], forOrganization=org,
             forOutcome=oc_youth, hasIndicatorReport=[rep_pct]),
        node("cids:Indicator", ind_uuid, hasName="Youth participants",
             hasDescription="Distinct young people who attended at least one workshop.", unitDescription="Participants",
             unit_of_measure=UNIT["countUnit"], forOrganization=org, forOutcome=oc_youth,
             hasIndicatorReport=[rep_space]),
        node("cids:Indicator", ind_tag, hasName="Volunteer hours",
             hasDescription="Hours given by community volunteers.", unitDescription="Hours",
             unit_of_measure=UNIT["unspecifiedUnit"], forOrganization=org, forOutcome=oc_community,
             hasIndicatorReport=[rep_plain]),
        report(rep_query, "Community workshops held 2024", ind_upper, "46", UNIT["countUnit"]),
        report(rep_pct, "Youth workshops held 2024", ind_lower, "31", UNIT["countUnit"]),
        report(rep_space, "Youth participants 2024", ind_uuid, "214", UNIT["countUnit"]),
        report(rep_plain, "Volunteer hours 2024", ind_tag, "1875", UNIT["unspecifiedUnit"]),
    ]
    return Capsule(
        id="V02-stable-uris",
        category="valid",
        title="IRIs that must survive unchanged",
        summary="Kestrel Community Arts Society (Basic tier). Every node uses a different style of IRI.",
        source="New. Based on the IRI problems in the Airtable sample exports (double slashes, spaces, mixed http/https).",
        covers=[
            "`http:` (not `https:`) IRI for the Organization.",
            "A port number (`:8443`), a `#fragment`, and a double slash (`//Outcome`).",
            "Two Indicators whose IRIs differ only by letter case and a trailing slash. They are different nodes.",
            "`urn:uuid:` and `tag:` IRIs.",
            "A query string with `&`, percent-encoded characters (`%C3%A9`) and an encoded space (`%20`).",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "Each IRI comes back byte-for-byte: no added or removed trailing slash, no lower-casing, no `http`→`https`, no decoding of `%C3%A9` or `%20`, no collapsing of `//`.",
            "`.../Indicator/Workshops` and `.../Indicator/workshops/` stay two separate Indicators.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


def v03_literal_fidelity() -> Capsule:
    b = "https://ruisseau-vert.example/"
    org, addr = b + "Organization/RuisseauVert/", b + "Address/RuisseauVert/"
    oc = b + "Outcome/AffordableHomes/"
    inds = {
        "HouseholdsHoused": ("Households housed ", "Households in co-op homes at year end. ᐃᓪᓗᐃᑦ means \"houses\" in Inuktitut.",
                             "Ménages", UNIT["countUnit"], ["48", "52", "55"]),
        "RentToIncome": ("Average rent as % of income", "Average monthly rent divided by household income.",
                         "Percent", UNIT["percentUnit"], ["27.50", "26.75", "26.00"]),
        "RentSubsidy": ("Rent subsidy paid", "Total rent subsidy paid, in dollars and cents.",
                        "CAD", UNIT["cad"], ["1250000.00", "1312500.50", "1378125.75"]),
        "EnergyChange": ("Change in energy use", "Year-over-year change in energy use per home. Negative means less energy used.",
                         "Percent change", UNIT["percentUnit"], ["-3.5", "-4.25", "-0.75"]),
    }
    periods = [
        ("2022", "2022-01-01T00:00:00-05:00", "2022-12-31T23:59:59-05:00"),
        ("2023", "2023-01-01T05:00:00Z", "2023-12-31T23:59:59.999-05:00"),
        ("2024", "2024-01-01T00:00:00-05:00", "2025-01-01T04:59:59+00:00"),
    ]
    long_text = (
        "Le Ruisseau-Vert est une coopérative fictive créée pour les tests de conformité CIDS. "
        "This description is deliberately long so that importers which cut text at 255 or 1000 characters are caught. "
        * 6
    ).strip()
    nodes = [
        node("cids:Organization", org, hasLegalName="Coopérative d’habitation du Ruisseau-Vert",
             hasAddress=[addr], hasOutcome=[oc], hasIndicator=[b + f"Indicator/{k}/" for k in inds]),
        node("cids:Address", addr, streetAddress="1200, rue de l’Exemple", addressLocality="Trois-Rivières",
             addressRegion="QC", postalCode="G9A 0A1", addressCountry="Canada"),
        sdg_theme(11),
        node("cids:Outcome", oc, hasName="Logements abordables — affordable homes",
             hasDescription=('Line 1: « Des logements sûrs ».\nLine 2: "Safe homes" & <stable> tenancy.\n'
                             "\tLine 3 starts with a tab."),
             forTheme=[SDG + "11"], forOrganization=org, hasIndicator=[b + f"Indicator/{k}/" for k in inds]),
    ]
    for slug, (name, desc, unit_desc, unit, values) in inds.items():
        ind = b + f"Indicator/{slug}/"
        reports = [b + f"IndicatorReport/{slug}/{p}" for p, *_ in periods]
        nodes.append(node("cids:Indicator", ind, hasName=name,
                          hasDescription=long_text if slug == "RentSubsidy" else desc,
                          unitDescription=unit_desc, unit_of_measure=unit, forOrganization=org,
                          forOutcome=oc, forTheme=[SDG + "11"], hasIndicatorReport=reports))
        for (label, start, end), rep, value in zip(periods, reports, values):
            nodes.append(node("cids:IndicatorReport", rep, hasName=f"{name}{label}",
                              value=measure(value, unit), startedAtTime=start, endedAtTime=end,
                              forIndicator=ind, forOrganization=org))
    return Capsule(
        id="V03-literal-fidelity",
        category="valid",
        title="Text, numbers and dates that must survive unchanged",
        summary="Coopérative d’habitation du Ruisseau-Vert (Basic tier). Values that importers often change by accident.",
        source="New. The Airtable samples had trailing spaces in names, which is a common place for data to change.",
        covers=[
            "French accents, a curly apostrophe (’), guillemets, an em dash, and Inuktitut syllabics.",
            "A description with line breaks, a tab, double quotes, `&` and `<...>`.",
            "A name with a trailing space (`\"Households housed \"`).",
            "A description longer than 1,000 characters.",
            "Number strings with trailing zeros (`\"27.50\"`, `\"1250000.00\"`) and negatives (`\"-0.75\"`).",
            "Dates written with `Z`, `+00:00`, and fractional seconds (`.999`).",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "Text is not trimmed, re-encoded, HTML-escaped or truncated.",
            "`hasNumericalValue` strings are not converted to numbers and back: `\"27.50\"` must not become `\"27.5\"` and `\"1250000.00\"` must not become `\"1250000\"` or `\"1.25E6\"`.",
            "Dates keep their written form. Converting `2023-01-01T05:00:00Z` to `2023-01-01T00:00:00-05:00` is the same instant. `compare` reports it as `LITERAL_REFORMATTED`, which only fails with `--strict`.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


def v04_uncommon_properties() -> Capsule:
    o = maple_hollow([2022, 2023, 2024])
    o.sff = False
    nodes = build_org(o)
    b = o.base
    org = find(nodes, o.org)
    ind = find(nodes, o.indicator("LearnersEnrolled"))
    outcome = find(nodes, o.outcome("ImprovedAdultLiteracy"))
    addr = find(nodes, o.iri("Address", o.slug))
    council = "https://literacy-standards.example/Organization/Council/"
    code_lit = "https://literacy-standards.example/Code/LIT-01"
    code_out = "https://literacy-standards.example/Code/OUT-ADULT"
    theme_lit = b + "Theme/AdultLiteracy/"
    theme_lifelong = b + "Theme/LifelongLearning/"
    contact = b + "Person/ProgramLead/"
    newcomers = b + "Characteristic/NewcomerLearners/"
    pop = b + "Population/AdultLearners"
    outcome2 = o.outcome("BetterJobProspects")

    org.update({
        "hasWebAddress": "https://maplehollow-learning.example/",
        "hasPurpose": "Free literacy classes for adults in Winnipeg.",
        "hasDescription": "A fictional learning collective used in the CIDS conformance tests.",
        "numberOfEmployees": 14,
        "hasContact": [contact],
        "hasCharacteristic": [newcomers],
    })
    org["hasOutcome"].append(outcome2)
    addr.update({"extendedAddress": "Suite 210", "postOfficeBoxNumber": "PO Box 4417"})
    outcome.update({"hasCode": [code_out], "canProduce": [outcome2]})
    ind.update({
        "hasIdentifier": "MH-IND-001",
        "hasCode": [code_lit],
        "definedBy": council,
        "cids:describesPopulation": {"@id": pop},
        "forTheme": [SDG + "4", theme_lit],
        "hasBaseline": measure("150", UNIT["countUnit"]),
        "hasThreshold": measure("200", UNIT["countUnit"]),
    })
    first = find(nodes, o.report("LearnersEnrolled", "2022"))
    first["cids:hasComment"] = [
        "Enrolment includes the spring intake only.",
        "Figures checked against the attendance register.",
    ]

    nodes += [
        node(["cids:StandardsOrganization", "cids:Organization"], council,
             hasLegalName="Example Literacy Standards Council"),
        node("cids:Code", code_lit, hasName="Adult learners enrolled (LIT-01)",
             hasDescription="Standard indicator code for adult literacy enrolment.",
             definedBy=council, hasIdentifier="LIT-01",
             hasSpecification="https://literacy-standards.example/spec/LIT-01",
             **{"sch:codeValue": "LIT-01"}),
        node("cids:Code", code_out, hasName="Adult literacy outcome (OUT-ADULT)",
             hasDescription="Standard outcome code for adult literacy.", definedBy=council,
             **{"sch:codeValue": "OUT-ADULT"}),
        node("cids:Theme", theme_lit, hasName="Adult literacy",
             hasDescription="Reading, writing and numeracy for adults.", relatesTo=[theme_lifelong],
             hasCode=[code_out]),
        node("cids:Theme", theme_lifelong, hasName="Lifelong learning",
             hasDescription="Learning at every stage of life."),
        node("cids:Person", contact, givenName="Noor", familyName="Haddad",
             hasEmail="noor.haddad@maplehollow-learning.example"),
        node("cids:Characteristic", newcomers, hasName="Learners who are newcomers to Canada",
             hasDescription="Learners who arrived in Canada in the last five years."),
        node("i72:Population", pop, label="Adult learners"),
        node("cids:Outcome", outcome2, hasName="Better job prospects",
             hasDescription="Learners qualify for jobs that need a literacy certificate.",
             forOrganization=o.org),
    ]
    return Capsule(
        id="V04-uncommon-properties",
        category="valid",
        title="Less common CIDS properties",
        summary=("Maple Hollow Learning Collective (Basic tier plus optional properties). Uses properties that are "
                 "valid CIDS but rarely appear in Basic tier exports, so importers often drop them."),
        source="New. There was no agreed list of uncommon properties, so these were picked from the CIDS ontology and the SFF/Full tier shapes.",
        covers=[
            "Organization: `hasWebAddress`, `hasPurpose`, `hasDescription`, `numberOfEmployees`, `hasContact` → Person, `hasCharacteristic`, `hasID` → OrganizationID.",
            "Address: `extendedAddress`, `postOfficeBoxNumber`.",
            "Indicator: `hasIdentifier`, `hasCode` → Code, `definedBy`, `cids:describesPopulation` → i72:Population (no context term, so a prefixed key), `hasBaseline` and `hasThreshold` (each an i72:Measure), and two `forTheme` values.",
            "Outcome: `hasCode`, `canProduce` → another Outcome.",
            "Theme: `relatesTo` → another Theme, `hasCode`.",
            "Code: `definedBy`, `hasIdentifier`, `hasSpecification` (xsd:anyURI), `schema:codeValue`.",
            "A node with two types (`cids:StandardsOrganization` and `cids:Organization`).",
            "IndicatorReport with two `cids:hasComment` values.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "All of the properties listed above come back, with their values.",
            "`hasBaseline` and `hasThreshold` come back as Measures with both `hasNumericalValue` and `unit_of_measure`.",
            "The comments come back as `cids:hasComment`. **Watch out:** the SFF context maps the short key `hasComment` to `sff:hasComment`, so an exporter that writes `\"hasComment\"` with both contexts loaded produces the wrong property. `compare` reports this as `PREDICATE_CHANGED`.",
            "The Council node keeps both of its types.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


def v05_sff_full() -> Capsule:
    o = riverbend()
    nodes = build_org(o)
    pop = o.base + "Population/MemberHouseholds"
    # No context term for describesPopulation: written as a prefixed key.
    find(nodes, o.indicator("MembersServed"))["cids:describesPopulation"] = {"@id": pop}
    nodes.append(node("i72:Population", pop, label="Member households"))
    units = [
        ("tonne", "i72:Singular_unit", "Tonne", "t"),
        ("megawattHour", "i72:Unit_multiplication", "Megawatt-hour", "MWh"),
        ("countUnit", "i72:Cardinality_unit", "Count", "count"),
    ]
    for key, type_, label, symbol in units:
        nodes.append({"@context": nodes[0]["@context"], "@id": UNIT[key], "label": label,
                      "@type": type_, "i72:symbol": symbol})
    return Capsule(
        id="V05-sff-full",
        category="valid",
        title="Full, realistic SFF capsule for one organization",
        summary=("Riverbend Community Energy Co-operative: every SFF node type, three Indicators with seven years "
                 "of annual reports (2019-2025), shaped like the Airtable sample exports."),
        source="Rebuilt from the shape of SampleOrg1.json (2025 sample set) with fictional data and the defects fixed.",
        covers=[
            "Organization, Address, OrganizationID (CRA business number), Person, OrganizationProfile, two TeamProfiles with EDGProfiles, FundingStatus, ReportInfo.",
            "SFF codelist references: sector, locality, province, population served, organization type, funding state, equity-deserving groups.",
            "Theme nodes for SDG 7 and 13, with the same names as the SDG codelist.",
            "Unit definitions (`i72:Singular_unit` etc.) and an `i72:Population`, as in the Airtable exports.",
            "An Indicator linked to two Outcomes.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "All 21 IndicatorReports come back with their exact values and periods.",
            "Codelist IRIs (`https://codelist.commonapproach.org/...`, `https://metadata.un.org/sdg/...`) come back exactly. They are not swapped for labels.",
            "`hasTeamSize`, `hasEDGSize` and `hasSize` stay `xsd:nonNegativeInteger`, and `reportedDate` stays `xsd:dateTime`.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


def v06_incremental_import() -> Capsule:
    early, late = list(range(2019, 2025)), [2025]
    part1 = []
    for make in (northwind, maple_hollow, prairie_spoke):
        part1 += build_org(make(early, profile_year=2024))
    part2 = []
    for make in (northwind, maple_hollow, prairie_spoke):
        part2 += build_org(make(late, profile_year=2025))
    merged = merge_nodes(part1, part2)
    return Capsule(
        id="V06-portfolio-incremental-import",
        category="valid",
        title="Three organizations, imported in two steps",
        summary=("A three-organization portfolio. Part 1 has every year up to 2024, part 2 has only 2025. "
                 "Importing both must give the same result as importing the merged file."),
        source=("2025 sample set notes: \"preload Multiple Orgs for all years up to 2024, then import Multiple Orgs "
                "only recent years\". Rebuilt with fictional organizations."),
        covers=[
            "Several organizations in one capsule.",
            "Adding a new year to data that is already loaded: same Organization, Outcome and Indicator IRIs, new IndicatorReports and new dated SFF profiles.",
            "Indicators whose `hasIndicatorReport` list grows between imports.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "Import `part-1-up-to-2024.jsonld`, then export. The export must match part 1.",
            "Then import `part-2-2025.jsonld` on top, and export again. The export must match `expected-after-both-parts.jsonld`: nothing from part 1 is lost or duplicated, and the 2025 data is added.",
            "Shared nodes (Organizations, Outcomes, Indicators, Addresses) are updated in place, not created again under a new IRI.",
        ],
        files=[
            CapsuleFile("part-1-up-to-2024.jsonld", part1, description="Reports for 2019-2024; 2024 SFF profiles."),
            CapsuleFile("part-2-2025.jsonld", part2, description="Reports for 2025 only; 2025 SFF profiles."),
            CapsuleFile("expected-after-both-parts.jsonld", merged, description="Part 1 and part 2 merged."),
        ],
    )


def _quarters(years, values):
    # Atlantic time: AST -04:00 in winter, ADT -03:00 from mid-March to early November.
    q = [("Q1", "01-01T00:00:00-04:00", "03-31T23:59:59-03:00"),
         ("Q2", "04-01T00:00:00-03:00", "06-30T23:59:59-03:00"),
         ("Q3", "07-01T00:00:00-03:00", "09-30T23:59:59-03:00"),
         ("Q4", "10-01T00:00:00-03:00", "12-31T23:59:59-04:00")]
    out = []
    for y in years:
        for label, s, e in q:
            out.append((f"{y}-{label}", f"{y}-{s}", f"{y}-{e}"))
    return [(p, s, e, v) for (p, s, e), v in zip(out, values)]


def v07_quarterly() -> Capsule:
    b = "https://harbourlight-health.example/"
    o = OrgSpec(
        base=b, slug="Harbourlight", legal_name="Harbourlight Health Navigation Inc.",
        street="55 Hypothetical Wharf", city="Halifax", region="NS", postal_code="B3J 0A7",
        business_number="678912345RC0001",
        contact=("Casey", "MacNeil", "casey.macneil@harbourlight-health.example"),
        sdgs=[3],
        outcomes=[OutcomeSpec("FewerHospitalDays", "Fewer avoidable hospital days",
                              "Patients get care at home instead of waiting in hospital.", themes=[SDG + "3"])],
        indicators=[
            IndicatorSpec("PatientsSupported", "Patients supported", "Patients who received navigation support in the quarter.",
                          "Patients", UNIT["countUnit"], ["FewerHospitalDays"],
                          _quarters([2024, 2025], ["412", "438", "451", "470", "486", "502", "519"]),
                          themes=[SDG + "3"]),
            IndicatorSpec("HospitalDaysAvoided", "Hospital days avoided", "Estimated hospital bed-days avoided in the year.",
                          "Days", UNIT["dayUnit"], ["FewerHospitalDays"],
                          annual_series([2022, 2023, 2024], ["2950", "3310", "3605"], tz="-04:00"),
                          themes=[SDG + "3"]),
        ],
        sectors=["Health"], provinces=["NS"], localities=["loc1", "loc4"],
        populations=["ps19", "ps18"], org_types=["forProfit"],
        mgmt=(5, 2, [("edg10", 2)]), board=(6, 3, [("edg2", 1), ("edg10", 2)]),
        report_period=("2025-Q3", "2025-07-01T00:00:00-03:00", "2025-09-30T23:59:59-03:00"),
        profile_date="2025-10-15T00:00:00-03:00", team_date="2025-10-15T00:00:00-03:00",
    )
    return Capsule(
        id="V07-quarterly-reporting",
        category="valid",
        title="A portfolio organization that reports by quarter",
        summary=("Harbourlight Health Navigation Inc. (SFF). One Indicator has seven quarterly reports "
                 "(2024-Q1 to 2025-Q3), another has annual reports, and the ReportInfo covers one quarter."),
        source="Gap listed in the 2025 sample set notes: \"portfolio organizations that report by quarter\".",
        covers=[
            "Quarterly `startedAtTime`/`endedAtTime` periods next to annual ones in the same capsule.",
            "UTC offsets that change at daylight-saving time (-04:00 in winter, -03:00 in summer).",
            "A ReportInfo for a quarter, not a year.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "Each quarterly report keeps its own start and end. Reports are not merged into years and periods are not snapped to calendar years.",
            "UTC offsets are preserved as written (strict mode), or at least the same instant is kept (default mode).",
        ],
        files=[CapsuleFile("capsule.jsonld", build_org(o))],
    )


def _fiscal(years, start_md, end_md, tz_start, tz_end, values):
    out = []
    for y, v in zip(years, values):
        label = f"FY{y}-{str(y + 1)[2:]}"
        out.append((label, f"{y}-{start_md}T00:00:00{tz_start}", f"{y + 1}-{end_md}T23:59:59{tz_end}", v))
    return out


def v08_mismatched_year_ends() -> Capsule:
    a = OrgSpec(
        base="https://silverbirch-family.example/", slug="Silverbirch",
        legal_name="Silverbirch Family Services", street="9 Mock Street", city="Fredericton",
        region="NB", postal_code="E3B 0A8", business_number="789123456RC0001",
        contact=("Taylor", "Arsenault", "taylor.arsenault@silverbirch-family.example"),
        sdgs=[1],
        outcomes=[OutcomeSpec("StableHousing", "Families in stable housing",
                              "Families at risk of eviction keep their homes.", themes=[SDG + "1"])],
        indicators=[IndicatorSpec(
            "FamiliesSupported", "Families supported", "Families who received a housing support plan.",
            "Families", UNIT["countUnit"], ["StableHousing"],
            _fiscal([2022, 2023, 2024], "04-01", "03-31", "-03:00", "-03:00", ["188", "203", "219"]),
            themes=[SDG + "1"])],
        sectors=["RealEstate"], provinces=["NB"], localities=["loc2"], populations=["ps11", "ps15"],
        org_types=["Charitable"], mgmt=(3, 1, [("edg10", 1)]), board=(5, 2, [("edg10", 2)]),
        report_period=("FY2024-25", "2024-04-01T00:00:00-03:00", "2025-03-31T23:59:59-03:00"),
        profile_date="2025-06-30T00:00:00-03:00", team_date="2025-06-30T00:00:00-03:00",
    )
    b = OrgSpec(
        base="https://lakeshore-repair.example/", slug="Lakeshore",
        legal_name="Lakeshore Repair Café Co-operative", street="300 Pretend Boulevard", city="Kingston",
        region="ON", postal_code="K7L 0A9", business_number="891234567RC0001",
        contact=("Jamie", "Kowalczyk", "jamie.kowalczyk@lakeshore-repair.example"),
        sdgs=[12],
        outcomes=[OutcomeSpec("LessWaste", "Fewer items thrown away",
                              "Broken items are repaired instead of replaced.", themes=[SDG + "12"])],
        indicators=[IndicatorSpec(
            "ItemsRepaired", "Items repaired", "Household items repaired at repair events.",
            "Items", UNIT["countUnit"], ["LessWaste"],
            _fiscal([2022, 2023, 2024], "07-01", "06-30", "-04:00", "-04:00", ["1320", "1475", "1590"]),
            themes=[SDG + "12"])],
        sectors=["Waste"], provinces=["ON"], localities=["loc2"], populations=["ps25"],
        org_types=["Cooperative"], mgmt=(2, 1, [("edg3", 1)]), board=(5, 2, [("edg10", 2)]),
        report_period=("FY2024-25", "2024-07-01T00:00:00-04:00", "2025-06-30T23:59:59-04:00"),
        profile_date="2025-08-29T00:00:00-04:00", team_date="2025-08-29T00:00:00-04:00",
    )
    return Capsule(
        id="V08-mismatched-year-ends",
        category="valid",
        title="Organizations with different fiscal year ends",
        summary=("Two SFF organizations in one capsule: Silverbirch Family Services reports April-March, and "
                 "Lakeshore Repair Café Co-operative reports July-June."),
        source="Gap listed in the 2025 sample set notes: \"mismatched year ends\".",
        covers=[
            "Report periods that cross calendar years (e.g. 2023-04-01 to 2024-03-31).",
            "Two different fiscal calendars in one capsule.",
            "ReportInfo periods that match each organization's fiscal year.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "Report periods are kept exactly. They are not moved to calendar years or relabelled by the year they end in.",
            "Each organization keeps its own reports. Same-named periods (both have a `FY2024-25`) are not merged across organizations.",
        ],
        files=[CapsuleFile("capsule.jsonld", build_org(a) + build_org(b))],
    )


def v09_bcorp_indicator_hascode() -> Capsule:
    o = OrgSpec(
        base="https://driftwood-gear.example/", slug="Driftwood",
        legal_name="Driftwood Outdoor Gear Inc.", street="18 Sample Quay", city="Victoria",
        region="BC", postal_code="V8W 0A2", business_number="912345678RC0001",
        contact=("Riley", "Chen", "riley.chen@driftwood-gear.example"),
        sdgs=[12],
        outcomes=[OutcomeSpec("ResponsibleBusiness", "Responsible business practices",
                              "The company is run in a way that benefits workers, community and environment.",
                              themes=[SDG + "12"])],
        indicators=[IndicatorSpec(
            "BImpactAssessment", "B Impact Assessment overall score",
            "Overall score from the company's B Impact Assessment (0-200 scale).",
            "Points", UNIT["scoreUnit"], ["ResponsibleBusiness"],
            annual_series([2021, 2022, 2023, 2024, 2025], ["84.6", "86.2", "89.0", "91.3", "92.8"], tz="-08:00"),
            themes=[SDG + "12"])],
        # Not "CrossCategory": that IRIS category isn't typed cids:Sector in ESDCSector.ttl.
        sectors=["Climate", "Waste"], provinces=["BC"], localities=["loc1"], populations=["ps25"],
        org_types=["forProfit"], mgmt=(4, 2, [("edg10", 2)]), board=(5, 2, [("edg8", 1), ("edg10", 1)]),
        report_period=("2025", "2025-01-01T00:00:00-08:00", "2025-12-31T23:59:59-08:00"),
        profile_date="2026-01-31T00:00:00-08:00", team_date="2026-01-31T00:00:00-08:00",
    )
    nodes = build_org(o)
    code = "https://cids-conformance.example/Code/BImpactAssessmentOverallScore"
    blab = "https://cids-conformance.example/Organization/BLab/"
    find(nodes, o.indicator("BImpactAssessment"))["hasCode"] = [code]
    nodes += [
        node(["cids:StandardsOrganization", "cids:Organization"], blab, hasLegalName="B Lab"),
        node("cids:Code", code, hasName="B Impact Assessment overall score",
             hasDescription="The overall score a company earns on the B Impact Assessment. Scores run from 0 to 200; 80 or more is needed for B Corp certification.",
             definedBy=blab, **{"sch:codeValue": "BIA-OVERALL"}),
    ]
    return Capsule(
        id="V09-bcorp-indicator-hascode",
        category="valid",
        title="B Corp assessment as an Indicator with hasCode",
        summary=("Driftwood Outdoor Gear Inc. (SFF). The B Impact Assessment score is an Indicator with a "
                 "`hasCode` link to a Code that identifies it as the standard B Impact score, plus five annual reports."),
        source=("Gap listed in the 2025 sample set notes: \"BCorp Assessments as Indicator + hasCode\". In the "
                "Airtable samples the B Corp reports had no Indicator at all."),
        covers=[
            "`cids:hasCode` on an Indicator, pointing to a `cids:Code` with `definedBy` and `schema:codeValue`.",
            "A standards organization typed as both `cids:StandardsOrganization` and `cids:Organization`.",
            "Decimal scores in `hasNumericalValue` with `cids:scoreUnit`.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + [
            "The Indicator keeps its `hasCode` link, and the Code node comes back with all its properties.",
            "Every B Impact report stays linked to the Indicator with `forIndicator`.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


def tier_roundtrip(nodes: list[dict]) -> list[str]:
    """Round-trip promises for the tier capsules, naming the prefixed keys
    this capsule actually uses."""
    prefixed = sorted({k for n in nodes for k in n if ":" in k and not k.startswith("@")})
    return [
        "These properties are written as prefixed keys, because the CIDS/SFF contexts have no term for them "
        "(or, for `cids:hasComment`, the SFF term means something else). They must all come back: " + ", ".join(f"`{k}`" for k in prefixed) + ". "
        "An importer that only maps context terms will drop them silently.",
        "`cids:hasComment` stays `cids:hasComment`. It must not turn into `sff:hasComment` "
        "(the SFF context maps the short key `hasComment` to `sff:hasComment`).",
        "Measures keep their IRIs. They are not turned into blank nodes or nested copies "
        "(the Essential tier requires `i72:value` to point at an IRI).",
        "`isUnderserved` stays an `xsd:boolean`, and enumerated values such as `hasCatchmentArea: \"local\"` keep their exact text.",
    ]


def v10_essential_tier() -> Capsule:
    nodes = essential_tier_nodes()
    return Capsule(
        id="V10-essential-tier",
        category="valid",
        title="Full, realistic Essential tier capsule",
        summary=("Harbourlight Community Kitchen Society: a training kitchen with two Outcomes, two Indicators "
                 "(one linked to both Outcomes) and three years of reports, with everything the Essential tier asks for: "
                 "targets, baselines, stakeholders, stakeholder outcomes and impact reports."),
        source="New. The 2025 sample set is all Basic tier or SFF; the updated ticket asks for an Essential tier capsule.",
        profiles=ESSENTIAL,
        covers=[
            "The core Essential tier classes: Organization, Address, Outcome, Indicator, IndicatorReport, Target, "
            "Theme, Code, StandardsOrganization, Stakeholder, Characteristic, StakeholderOutcome, ImpactReport, "
            "ImpactScale, ImpactDepth, ImpactDuration, Measure. (BeneficialStakeholder, ContributingStakeholder and "
            "ImpactPathway are in V11.)",
            "Indicators with `definedBy` (the organization itself, or a standards body), `hasBaseline` and `cids:hasTarget`.",
            "Each IndicatorReport points to that year's Target with `cids:forTarget`, and the Target points back.",
            "A Code with `hasSpecification` (`xsd:anyURI`), `sch:codeValue` and a value.",
            "Measures with their own IRIs instead of blank nodes.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + tier_roundtrip(nodes) + [
            "\"Community meals served\" comes back as one Indicator with both `forOutcome` links.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


def v11_full_tier() -> Capsule:
    nodes = full_tier_nodes()
    return Capsule(
        id="V11-full-tier",
        category="valid",
        title="Full, realistic Full tier capsule",
        summary=("Cedarline Home Retrofit Co-operative (SFF): a complete impact model, with a program, service, "
                 "activities, inputs, outputs, beneficial and contributing stakeholders, a counterfactual, an impact "
                 "risk and a stakeholder report, as well as Outcomes, Indicators, reports and targets."),
        source="New. The 2025 sample set is all Basic tier or SFF; the updated ticket asks for a Full tier capsule.",
        profiles=FULL,
        covers=[
            "ImpactPathway (also typed ImpactModel), Program, Service, three Activities, an Input with planned and "
            "actual amounts and a Resource type, an Output.",
            "BeneficialStakeholder and ContributingStakeholder (each also typed Stakeholder), with `benefitsFrom`, "
            "`cids:contributes` and `cids:performs`.",
            "StakeholderOutcome with `fromPerspectiveOf`, `hasImportance` and `intendedImpact`.",
            "ImpactReport with scale, depth and duration, `hasExpectation`, `hasReportedImpact` and an EvidenceRisk "
            "(also typed ImpactRisk); a Counterfactual.",
            "Indicators with `hasThreshold`, `hasIdentifier`, `hasAccess` and `prov:wasGeneratedBy`.",
            "StakeholderReport with a CharacteristicReport.",
            "`sch:dateCreated` and `description` on every CIDS node, and the SFF profile nodes (OrganizationProfile, "
            "TeamProfiles, EDGProfiles, FundingStatus, ReportInfo).",
            "Also passes the Essential tier shapes.",
        ],
        roundtrip=GENERAL_ROUNDTRIP + tier_roundtrip(nodes) + [
            "Nodes with two types (`cids:BeneficialStakeholder` + `cids:Stakeholder`, `cids:EvidenceRisk` + "
            "`cids:ImpactRisk`, `cids:ImpactPathway` + `cids:ImpactModel`) keep both types.",
            "`cids:beneficialSizeStart` / `cids:beneficialSizeEnd` stay `xsd:positiveInteger`.",
            "\"Homes retrofitted\" comes back as one Indicator with both `forOutcome` links.",
        ],
        files=[CapsuleFile("capsule.jsonld", nodes)],
    )


# ==========================================================================
# Broken capsules (SHACL violations) - all start from the Tamarack base
# ==========================================================================

def _base():
    o = tamarack()
    return o, build_org(o)


def _iri(o: OrgSpec):
    return {
        "org": o.org,
        "address": o.iri("Address", o.slug),
        "orgid": o.iri("OrganizationID", o.slug),
        "profile": o.iri("OrganizationProfile", o.slug, o.profile_date[:4]),
        "person": o.iri("Person", f"{o.slug}Contact"),
        "mgmt": o.iri("TeamProfile", o.slug, "Management", o.team_date[:4]),
        "reportinfo": o.iri("ReportInfo", o.slug, o.report_period[0]),
        "jobs": o.indicator("YouthPlacedInJobs"),
        "bia": o.indicator("BImpactScore"),
        "outcome": o.outcome("YouthInStableEmployment"),
    }


INVALID_IMPORTER = ("An importer should reject this capsule, or import it while clearly reporting the problem described above. "
                    "It must not quietly fix or drop the bad data.")
DQ_IMPORTER = ("The capsule passes SHACL validation, so an importer can accept it. A good importer (or a "
               "validator run before import) should warn the user about the finding listed above. "
               "It should still import and export the data unchanged.")


def i01_missing_postal_code() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["address"])["postalCode"]
    return Capsule(
        id="I01-address-missing-postal-code", category="invalid",
        title="Address with no postal code",
        summary="The Address has a street, city, province and country, but no `postalCode`.",
        source="SPO2incompleteaddressnopostalcode20261103.json",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["address"], "cids:postalCode", "MinCount",
                  "Every Address needs exactly one postalCode."),
        ])],
    )


def i02_measure_missing_value() -> Capsule:
    o, nodes = _base()
    rep = o.report("YouthPlacedInJobs", "2022")
    del find(nodes, rep)["value"]["hasNumericalValue"]
    return Capsule(
        id="I02-report-value-missing-number", category="invalid",
        title="IndicatorReport value with no number",
        summary="The 2022 \"Youth placed in jobs\" report has a `value` Measure with a unit but no `hasNumericalValue`.",
        source="SPO8indicatorreportwithmissingvalues20261103.json",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(f"{rep} / i72:value", "i72:hasNumericalValue", "MinCount",
                  "The Measure behind a report's value needs exactly one hasNumericalValue."),
        ])],
    )


def i03_identifier_missing_values() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    oid = find(nodes, i["orgid"])
    del oid["hasIdentifier"], oid["issuedBy"]
    return Capsule(
        id="I03-organization-id-missing-values", category="invalid",
        title="OrganizationID with no identifier and no issuer",
        summary="The OrganizationID node exists but has neither `hasIdentifier` nor `issuedBy`.",
        source="SPO10identifiermissingvalues20261103.json",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["orgid"], "org:hasIdentifier", "MinCount",
                  "An OrganizationID needs the identifier itself (e.g. the business number).", SFF_ONLY),
            Shacl(i["orgid"], "org:issuedBy", "MinCount",
                  "An OrganizationID needs the organization that issued it (e.g. Canada Revenue Agency).", SFF_ONLY),
        ])],
    )


def i04_invalid_date() -> Capsule:
    o, nodes = _base()
    rep = o.report("YouthPlacedInJobs", "2024")
    find(nodes, rep)["endedAtTime"] = "Invalid date"
    return Capsule(
        id="I04-invalid-date", category="invalid",
        title="\"Invalid date\" as a report's end date",
        summary="The 2024 \"Youth placed in jobs\" report's `endedAtTime` is the text \"Invalid date\" instead of a date and time.",
        source="All of the SPO*.json samples have \"Invalid date\" in date fields (a spreadsheet export artifact). "
               "I12 covers the same text in `reportedDate`.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(rep, "prov:endedAtTime", "Datatype", "endedAtTime must be an xsd:dateTime."),
        ])],
    )


def i12_invalid_reported_date() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    find(nodes, i["profile"])["reportedDate"] = "Invalid date"
    return Capsule(
        id="I12-invalid-reported-date", category="invalid",
        title="\"Invalid date\" as an OrganizationProfile's reportedDate",
        summary="The OrganizationProfile's `reportedDate` is the text \"Invalid date\" instead of a date and time.",
        source="SPO*.json: every SPO sample has `reportedDate: \"Invalid date\"` (a spreadsheet export artifact).",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["profile"], "sff:reportedDate", "Datatype",
                  "reportedDate must be an xsd:dateTime such as 2025-03-31T00:00:00-04:00.", SFF_ONLY),
        ])],
    )


def i05_report_without_indicator() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    rep = o.report("BImpactScore", "2019")
    del find(nodes, rep)["forIndicator"]
    find(nodes, i["bia"])["hasIndicatorReport"].remove(rep)
    return Capsule(
        id="I05-report-without-indicator", category="invalid",
        title="IndicatorReport not linked to any Indicator",
        summary="The 2019 B Impact report has no `forIndicator`, and no Indicator lists it.",
        source="The B Corp reports in the Airtable sample exports (SampleOrg*, MultipleOrgs*) have no forIndicator.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(rep, "cids:forIndicator", "MinCount",
                  "Every IndicatorReport must say which Indicator it reports on."),
        ])],
    )


UNDEFINED_SOURCE = "Several SPO samples and MultipleOrgs*.json reference Indicators and Outcomes that are never defined."


def i06_undefined_indicator() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    missing_ind = o.indicator("MentorHoursLogged")
    find(nodes, i["org"])["hasIndicator"].append(missing_ind)
    return Capsule(
        id="I06-undefined-indicator", category="invalid",
        title="Link to an Indicator that isn't in the capsule",
        summary="The Organization's `hasIndicator` lists an Indicator that is not defined anywhere in the capsule.",
        source=UNDEFINED_SOURCE + " I13 covers an undefined Outcome.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["org"], "cids:hasIndicator", "Class",
                  f"{missing_ind} is not defined as a cids:Indicator in the capsule."),
        ])],
    )


def i13_undefined_outcome() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    missing_out = o.outcome("HigherYouthIncomes")
    find(nodes, i["jobs"])["forOutcome"] = [i["outcome"], missing_out]
    return Capsule(
        id="I13-undefined-outcome", category="invalid",
        title="Link to an Outcome that isn't in the capsule",
        summary="An Indicator's `forOutcome` lists an Outcome that is not defined anywhere in the capsule.",
        source=UNDEFINED_SOURCE + " I06 covers an undefined Indicator.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["jobs"], "cids:forOutcome", "Class",
                  f"{missing_out} is not defined as a cids:Outcome in the capsule."),
        ])],
    )


def i07_empty_report_info() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    ri = find(nodes, i["reportinfo"])
    for k in ("hasName", "startedAtTime", "endedAtTime"):
        del ri[k]
    return Capsule(
        id="I07-empty-report-info", category="invalid",
        title="ReportInfo with only an organization",
        summary="The ReportInfo node has `forOrganization` but no name and no reporting period.",
        source="Every ReportInfo in the Airtable sample exports looks like this.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["reportinfo"], "org:hasName", "MinCount", "ReportInfo needs a name.", SFF_ONLY),
            Shacl(i["reportinfo"], "prov:startedAtTime", "MinCount", "ReportInfo needs the start of the reporting period.", SFF_ONLY),
            Shacl(i["reportinfo"], "prov:endedAtTime", "MinCount", "ReportInfo needs the end of the reporting period.", SFF_ONLY),
        ])],
    )


def i08_indicator_missing_unit_description() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["bia"])["unitDescription"]
    return Capsule(
        id="I08-indicator-missing-unit-description", category="invalid",
        title="Indicator with no unit description",
        summary="The B Impact Indicator has no `unitDescription`.",
        source="New. A required Basic tier field that spreadsheet exports often leave blank. I14 covers a missing `forOrganization`.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["bia"], "cids:unitDescription", "MinCount", "Every Indicator needs a unitDescription."),
        ])],
    )


def i14_indicator_missing_organization() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["bia"])["forOrganization"]
    return Capsule(
        id="I14-indicator-missing-organization", category="invalid",
        title="Indicator with no organization",
        summary="The B Impact Indicator has no `forOrganization`. The Organization still lists it in `hasIndicator`.",
        source="New. A required Basic tier field that spreadsheet exports often leave blank. I08 covers a missing `unitDescription`.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["bia"], "cids:forOrganization", "MinCount", "Every Indicator must say which Organization it belongs to."),
        ])],
    )


def i09_report_two_indicators() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    rep = o.report("BImpactScore", "2024")
    find(nodes, rep)["forIndicator"] = [i["bia"], i["jobs"]]
    find(nodes, i["jobs"])["hasIndicatorReport"].append(rep)
    return Capsule(
        id="I09-report-for-two-indicators", category="invalid",
        title="One IndicatorReport claimed by two Indicators",
        summary="The 2024 B Impact report has two `forIndicator` values, and both Indicators list it in `hasIndicatorReport`.",
        source="SPO16 in MultipleOrgs*.json: one report is listed under two Indicators. A merge of duplicate Indicators produces the same thing.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(rep, "cids:forIndicator", "MaxCount", "An IndicatorReport reports on exactly one Indicator."),
        ])],
    )


def i10_negative_team_size() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    find(nodes, i["mgmt"])["hasTeamSize"] = -3
    return Capsule(
        id="I10-negative-team-size", category="invalid",
        title="Negative team size",
        summary="The management TeamProfile has `hasTeamSize: -3`.",
        source="New. Checks that importers enforce xsd:nonNegativeInteger.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["mgmt"], "sff:hasTeamSize", "Datatype",
                  "hasTeamSize must be a whole number of 0 or more.", SFF_ONLY),
        ])],
    )


def i11_missing_legal_name() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["org"])["hasLegalName"]
    return Capsule(
        id="I11-organization-missing-legal-name", category="invalid",
        title="Organization with no legal name",
        summary="The Organization node has no `hasLegalName`.",
        source="New.",
        importer=INVALID_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=None, shacl=[
            Shacl(i["org"], "org:hasLegalName", "MinCount", "Every Organization needs exactly one legal name."),
        ])],
    )


# ==========================================================================
# Data-quality capsules (SHACL-valid, flagged by DQ checks)
# ==========================================================================

def dq01_missing_address() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["org"])["hasAddress"]
    nodes = remove(nodes, i["address"])
    return Capsule(
        id="DQ01-missing-address", category="data-quality",
        title="Organization with no address",
        summary="The Organization has no `hasAddress` and there is no Address node.",
        source="SPO1missingaddress20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-MISSING-ADDRESS", i["org"], "cids:hasAddress",
               "hasAddress is optional in SHACL, but a reporting organization without an address is almost always a mistake."),
        ])],
    )


def dq02_missing_contact() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["profile"])["hasPrimaryContact"]
    nodes = remove(nodes, i["person"])
    return Capsule(
        id="DQ02-missing-primary-contact", category="data-quality",
        title="Organization profile with no primary contact",
        summary="The OrganizationProfile has no `hasPrimaryContact` and there is no Person node.",
        source="SPO4missingcontactperson20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-MISSING-CONTACT", i["profile"], "sff:hasPrimaryContact",
               "hasPrimaryContact is optional in SHACL, but SFF reports should name a contact person."),
        ])],
    )


def dq03_indicator_without_reports() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    new = o.indicator("MentorHoursLogged")
    find(nodes, i["org"])["hasIndicator"].append(new)
    find(nodes, i["outcome"])["hasIndicator"].append(new)
    nodes.append(node("cids:Indicator", new, hasName="Mentor hours logged",
                      hasDescription="Hours volunteer mentors spent with participants.",
                      unitDescription="Hours", unit_of_measure=UNIT["unspecifiedUnit"],
                      forOrganization=i["org"], forOutcome=i["outcome"]))
    return Capsule(
        id="DQ03-indicator-without-reports", category="data-quality",
        title="Indicator with no reports",
        summary="A third Indicator, \"Mentor hours logged\", is defined and linked, but has no IndicatorReports.",
        source="SPO3indicatorwithoutanyindicatorreports20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-INDICATOR-NO-REPORTS", new, "cids:hasIndicatorReport",
               "An Indicator with no reports carries no data. Usually the reports were lost or never entered."),
        ])],
    )


def dq04_missing_org_id() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    del find(nodes, i["org"])["hasID"]
    nodes = remove(nodes, i["orgid"])
    return Capsule(
        id="DQ04-missing-organization-id", category="data-quality",
        title="Organization with no identifier",
        summary="The Organization has no `hasID` and there is no OrganizationID node.",
        source="SPO9missingidentifier20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-MISSING-ORG-ID", i["org"], "org:hasID",
               "Without a business number or registry ID, the organization can't be matched across reports."),
        ])],
    )


def dq05_identifier_format() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    find(nodes, i["orgid"])["hasIdentifier"] = "123456789 RC0001 200"
    return Capsule(
        id="DQ05-malformed-business-number", category="data-quality",
        title="Business number in the wrong format",
        summary="The CRA business number is `\"123456789 RC0001 200\"`: it has spaces and extra digits.",
        source="SPO15identifierhaserrors20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-IDENTIFIER-FORMAT", i["orgid"], "org:hasIdentifier",
               "A CRA business number (BN15) is 9 digits, 2 letters and 4 digits, with no spaces, e.g. 123456789RC0001."),
        ])],
    )


def dq06_outlier() -> Capsule:
    o, nodes = _base()
    rep = o.report("BImpactScore", "2024")
    find(nodes, rep)["value"]["hasNumericalValue"] = "790"
    return Capsule(
        id="DQ06-outlier-value", category="data-quality",
        title="B Impact score far too high",
        summary="The 2024 B Impact score is 790. The other years are between 82 and 94, and the scale only goes to 200.",
        source="SPO5anomolousdataBScoretoohigh20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-OUTLIER", f"{rep} / i72:value", "i72:hasNumericalValue",
               "790 is more than 5 times the median of the other B Impact reports. Likely a typo (79.0?)."),
        ])],
    )


def dq07_time_series_gap() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    rep = o.report("YouthPlacedInJobs", "2022")
    nodes = remove(nodes, rep)
    find(nodes, i["jobs"])["hasIndicatorReport"].remove(rep)
    return Capsule(
        id="DQ07-time-series-gap", category="data-quality",
        title="Missing year in a time series",
        summary="\"Youth placed in jobs\" has annual reports for 2019-2024 except 2022.",
        source="SPO21missingdatainatimeseries2022missing20261103.json",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-TIME-SERIES-GAP", i["jobs"], "cids:hasIndicatorReport",
               "No report covers 2022, although there are reports before and after it."),
        ])],
    )


def dq08_empty_value() -> Capsule:
    o, nodes = _base()
    rep = o.report("BImpactScore", "2022")
    find(nodes, rep)["value"]["hasNumericalValue"] = ""
    return Capsule(
        id="DQ08-empty-numerical-value", category="data-quality",
        title="Empty value in an IndicatorReport",
        summary="The 2022 B Impact report has `hasNumericalValue: \"\"` (an empty string).",
        source=("SPO6missingvalueinanindicatorreportGallo20261103.json, SPO8... and SPO21... (2022 B Corp value). "
                "An empty string passes SHACL because hasNumericalValue is typed xsd:string."),
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-NON-NUMERIC-VALUE", f"{rep} / i72:value", "i72:hasNumericalValue",
               "The value is empty. Either remove the report or fill in the number."),
        ])],
    )


def dq09_address_swapped() -> Capsule:
    o, nodes = _base()
    i = _iri(o)
    a = find(nodes, i["address"])
    a["postalCode"], a["addressCountry"] = a["addressCountry"], a["postalCode"]
    return Capsule(
        id="DQ09-address-fields-swapped", category="data-quality",
        title="Postal code and country swapped",
        summary="The Address has `postalCode: \"Canada\"` and `addressCountry: \"P3E 0A1\"`.",
        source="Every Address in the Airtable sample exports (SampleOrg*, MultipleOrgs*) has these two fields swapped.",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-ADDRESS-FIELDS-SWAPPED", i["address"], "cids:postalCode",
               "Both fields are plain strings, so SHACL can't tell they are in the wrong places."),
        ])],
    )


def dq10_unknown_unit() -> Capsule:
    o, nodes = _base()
    rep = o.report("YouthPlacedInJobs", "2024")
    find(nodes, rep)["value"]["unit_of_measure"] = o.base + "Unit/Youth"
    return Capsule(
        id="DQ10-unknown-unit", category="data-quality",
        title="Unit of measure that isn't defined anywhere",
        summary="The 2024 \"Youth placed in jobs\" value uses the unit `https://tamarack-youth.example/Unit/Youth`, which is not in the CIDS units list or the capsule.",
        source="SPO21... uses `unit_of_measure: \"Days\"` (a label instead of a unit IRI, e.g. cids:dayUnit).",
        importer=DQ_IMPORTER,
        files=[CapsuleFile("capsule.jsonld", nodes, dq=[
            DQ("DQ-UNKNOWN-UNIT", f"{rep} / i72:value", "i72:unit_of_measure",
               "Use a unit from the CIDS units list (here cids:countUnit), or define the unit in the capsule."),
        ])],
    )


CAPSULES = [
    v01_indicator_multiple_outcomes, v02_stable_uris, v03_literal_fidelity, v04_uncommon_properties,
    v05_sff_full, v06_incremental_import, v07_quarterly, v08_mismatched_year_ends, v09_bcorp_indicator_hascode,
    v10_essential_tier, v11_full_tier,
    i01_missing_postal_code, i02_measure_missing_value, i03_identifier_missing_values, i04_invalid_date,
    i05_report_without_indicator, i06_undefined_indicator, i07_empty_report_info,
    i08_indicator_missing_unit_description, i09_report_two_indicators, i10_negative_team_size,
    i11_missing_legal_name, i12_invalid_reported_date, i13_undefined_outcome, i14_indicator_missing_organization,
    dq01_missing_address, dq02_missing_contact, dq03_indicator_without_reports, dq04_missing_org_id,
    dq05_identifier_format, dq06_outlier, dq07_time_series_gap, dq08_empty_value, dq09_address_swapped,
    dq10_unknown_unit,
]


def all_capsules() -> list[Capsule]:
    return [make() for make in CAPSULES]
