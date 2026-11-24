"""Fictional organizations used by the capsules.

Everything here is made up. Web and email domains use the reserved
``.example`` top-level domain (RFC 2606), so they can't belong to anyone.
Business numbers are 9 digits + RC + 4 digits but deliberately fail the CRA
check-digit test, so they can't be real.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import (
    CRA, UNIT, code_characteristic, edg, funding_state, locality, measure, node,
    org_type, population, province, sdg_theme, sector,
)


@dataclass
class IndicatorSpec:
    slug: str
    name: str
    description: str
    unit_description: str
    unit: str
    outcomes: list[str]
    series: list[tuple[str, str, str, str]]   # (period label, start, end, value)
    themes: list[str] = field(default_factory=list)
    report_name: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class OutcomeSpec:
    slug: str
    name: str
    description: str
    themes: list[str] = field(default_factory=list)


@dataclass
class OrgSpec:
    base: str                 # e.g. "https://tamarack-youth.example/"
    slug: str                 # e.g. "Tamarack"
    legal_name: str
    street: str
    city: str
    region: str
    postal_code: str
    business_number: str
    contact: tuple[str, str, str]                     # given, family, email
    outcomes: list[OutcomeSpec]
    indicators: list[IndicatorSpec]
    sdgs: list[int]
    sectors: list[str] = field(default_factory=list)
    provinces: list[str] = field(default_factory=list)
    localities: list[str] = field(default_factory=list)
    populations: list[str] = field(default_factory=list)
    org_types: list[str] = field(default_factory=list)
    mgmt: tuple[int, int, list[tuple[str, int]]] = (5, 2, [])   # size, EDG size, [(edg code, size)]
    board: tuple[int, int, list[tuple[str, int]]] = (7, 3, [])
    profile_date: str = "2025-03-31T00:00:00-04:00"
    team_date: str = "2025-03-31T00:00:00-04:00"
    report_period: tuple[str, str, str] = ("2024", "2024-01-01T00:00:00-05:00", "2024-12-31T23:59:59-05:00")
    funder: str = "Example Social Finance Fund"
    sff: bool = True          # include the SFF profile nodes

    # IRIs ---------------------------------------------------------------
    def iri(self, kind: str, *parts: str) -> str:
        tail = "/".join(parts)
        return f"{self.base}{kind}/{tail}/" if tail else f"{self.base}{kind}/"

    @property
    def org(self) -> str:
        return self.iri("Organization", self.slug)

    def outcome(self, slug: str) -> str:
        return self.iri("Outcome", slug)

    def indicator(self, slug: str) -> str:
        return self.iri("Indicator", slug)

    def report(self, ind: str, period: str) -> str:
        return f"{self.base}IndicatorReport/{ind}/{period}"


def build_org(o: OrgSpec) -> list[dict]:
    """All nodes for one organization, in a stable order."""
    nodes: list[dict] = []
    address = o.iri("Address", o.slug)
    org_id = o.iri("OrganizationID", o.slug)
    profile = o.iri("OrganizationProfile", o.slug, o.profile_date[:4])
    person = o.iri("Person", f"{o.slug}Contact")
    mgmt = o.iri("TeamProfile", o.slug, "Management", o.team_date[:4])
    board = o.iri("TeamProfile", o.slug, "Board", o.team_date[:4])
    funding = o.iri("FundingStatus", o.slug, o.profile_date[:4])
    report_info = o.iri("ReportInfo", o.slug, o.report_period[0])

    org = node(
        "cids:Organization", o.org,
        hasLegalName=o.legal_name,
        hasAddress=[address],
        hasID=[org_id],
        hasOutcome=[o.outcome(x.slug) for x in o.outcomes],
        hasIndicator=[o.indicator(x.slug) for x in o.indicators],
    )
    if o.sff:
        org["hasOrganizationProfile"] = [profile]
    nodes.append(org)

    nodes.append(node(
        "cids:Address", address,
        streetAddress=o.street, addressLocality=o.city, addressRegion=o.region,
        postalCode=o.postal_code, addressCountry="Canada",
    ))
    nodes.append(node(
        "org:OrganizationID", org_id,
        hasIdentifier=o.business_number, issuedBy=CRA, forOrganization=o.org,
    ))

    for sdg in o.sdgs:
        nodes.append(sdg_theme(sdg))

    for oc in o.outcomes:
        nodes.append(node(
            "cids:Outcome", o.outcome(oc.slug),
            hasName=oc.name, hasDescription=oc.description,
            forTheme=oc.themes or None,
            forOrganization=o.org,
            hasIndicator=[o.indicator(i.slug) for i in o.indicators if oc.slug in i.outcomes],
        ))

    for ind in o.indicators:
        outcomes = [o.outcome(s) for s in ind.outcomes]
        nodes.append(node(
            "cids:Indicator", o.indicator(ind.slug),
            hasName=ind.name, hasDescription=ind.description,
            unitDescription=ind.unit_description, unit_of_measure=ind.unit,
            forOrganization=o.org,
            forOutcome=outcomes if len(outcomes) != 1 else outcomes[0],
            forTheme=ind.themes or None,
            hasIndicatorReport=[o.report(ind.slug, p) for p, *_ in ind.series],
            **ind.extra,
        ))
        for period, start, end, value in ind.series:
            nodes.append(node(
                "cids:IndicatorReport", o.report(ind.slug, period),
                hasName=f"{ind.report_name or ind.name} {period}",
                value=measure(value, ind.unit),
                startedAtTime=start, endedAtTime=end,
                forIndicator=o.indicator(ind.slug), forOrganization=o.org,
            ))

    if not o.sff:
        return nodes

    nodes.append(node(
        "sff:OrganizationProfile", profile,
        forOrganization=o.org,
        reportedDate=o.profile_date,
        hasPrimaryContact=person,
        hasManagementTeamProfile=[mgmt],
        hasBoardProfile=[board],
        sectorServed=[sector(s) for s in o.sectors] or None,
        localityServed=[locality(s) for s in o.localities] or None,
        provinceTerritoryServed=[province(s) for s in o.provinces] or None,
        primaryPopulationServed=[population(s) for s in o.populations] or None,
        organizationType=[org_type(s) for s in o.org_types] or None,
        hasFundingStatus=[funding],
    ))
    given, family, email = o.contact
    nodes.append(node("cids:Person", person, givenName=given, familyName=family, hasEmail=email))

    for label, iri, (size, edg_size, groups) in (("Management", mgmt, o.mgmt), ("Board", board, o.board)):
        # Profiles are dated, so their IRIs include the year: a later report
        # adds new profiles instead of giving the old ones a second date.
        edg_iris = [o.iri("EDGProfile", o.slug, label, o.team_date[:4], code) for code, _ in groups]
        nodes.append(node(
            "sff:TeamProfile", iri,
            hasTeamSize=size, hasEDGSize=edg_size,
            hasEDGProfile=edg_iris or None,
            reportedDate=o.team_date,
        ))
        for (code, n), edg_iri in zip(groups, edg_iris):
            nodes.append(node("sff:EDGProfile", edg_iri, forEDG=edg(code), hasSize=n, reportedDate=o.team_date))

    nodes.append(node(
        "sff:FundingStatus", funding,
        forOrganization=o.org,
        hasFundingState=funding_state("funded"),
        forFunder=o.funder,
        hasDescription=f"Investment from the {o.funder}.",
        reportedDate=o.profile_date,
    ))
    nodes.append(node(
        "sff:ReportInfo", report_info,
        hasName=f"{o.legal_name} impact report {o.report_period[0]}",
        startedAtTime=o.report_period[1], endedAtTime=o.report_period[2],
        forOrganization=o.org,
    ))

    # Characteristic nodes for every population / EDG code referenced.
    codes = [population(c) for c in o.populations]
    codes += [edg(c) for _, _, groups in (o.mgmt, o.board) for c, _ in groups]
    for iri in dict.fromkeys(codes):
        nodes.append(code_characteristic(iri))
    return nodes


def merge_nodes(*node_lists: list[dict]) -> list[dict]:
    """Union of several node lists, merging nodes with the same @id
    (list-valued properties are unioned, in first-seen order)."""
    out: dict[str, dict] = {}
    for nodes in node_lists:
        for n in nodes:
            if n["@id"] not in out:
                out[n["@id"]] = {k: (list(v) if isinstance(v, list) else v) for k, v in n.items()}
                continue
            cur = out[n["@id"]]
            for k, v in n.items():
                if k in ("@context", "@id"):
                    continue
                if k not in cur:
                    cur[k] = v
                elif cur[k] != v:
                    a = cur[k] if isinstance(cur[k], list) else [cur[k]]
                    b = v if isinstance(v, list) else [v]
                    cur[k] = a + [x for x in b if x not in a]
    return list(out.values())


# --------------------------------------------------------------------------
# The organizations
# --------------------------------------------------------------------------

def annual_series(years, values, tz="-05:00") -> list[tuple[str, str, str, str]]:
    return [(str(y), f"{y}-01-01T00:00:00{tz}", f"{y}-12-31T23:59:59{tz}", v) for y, v in zip(years, values)]


SDG = "https://metadata.un.org/sdg/"


def tamarack(years=range(2019, 2025), bcorp=("82.4", "85.1", "88.9", "90.2", "93.6", "95.0")) -> OrgSpec:
    """Base for the broken and data-quality capsules: a youth employment
    social enterprise with two indicators (one of them a B Impact score,
    like the SPO samples)."""
    years = list(years)
    b = "https://tamarack-youth.example/"
    return OrgSpec(
        base=b, slug="Tamarack",
        legal_name="Tamarack Youth Employment Network",
        street="410 Sample Road", city="Sudbury", region="ON", postal_code="P3E 0A1",
        business_number="123456789RC0001",
        contact=("Robin", "Okafor", "robin.okafor@tamarack-youth.example"),
        sdgs=[8],
        outcomes=[OutcomeSpec("YouthInStableEmployment", "Youth in stable employment",
                              "Young people facing barriers find and keep stable jobs.",
                              themes=[SDG + "8"])],
        indicators=[
            IndicatorSpec("YouthPlacedInJobs", "Youth placed in jobs",
                          "Number of program participants who started a job lasting at least three months.",
                          "Youth", UNIT["countUnit"], ["YouthInStableEmployment"],
                          annual_series(years, ["112", "126", "131", "148", "155", "163"][: len(years)]),
                          themes=[SDG + "8"]),
            IndicatorSpec("BImpactScore", "B Impact Assessment score",
                          "Overall B Impact Assessment score.",
                          "Points", UNIT["scoreUnit"], ["YouthInStableEmployment"],
                          annual_series(years, list(bcorp)[: len(years)])),
        ],
        sectors=["Employment"], provinces=["ON"], localities=["loc2"],
        populations=["ps24"], org_types=["nonProfit"],
        mgmt=(4, 2, [("edg4", 1), ("edg10", 2)]),
        board=(7, 4, [("edg2", 1), ("edg10", 3)]),
    )


def riverbend() -> OrgSpec:
    """A community energy co-op with a long annual time series (2019-2025)."""
    b = "https://riverbend-energy.example/"
    years = list(range(2019, 2026))
    return OrgSpec(
        base=b, slug="Riverbend",
        legal_name="Riverbend Community Energy Co-operative",
        street="25 Placeholder Lane", city="Peterborough", region="ON", postal_code="K9J 0B2",
        business_number="234567891RC0001",
        contact=("Sam", "Lindqvist", "sam.lindqvist@riverbend-energy.example"),
        sdgs=[7, 13],
        outcomes=[
            OutcomeSpec("ReducedGHGEmissions", "Reduced greenhouse gas emissions",
                        "Members' homes and the local grid emit less greenhouse gas.", themes=[SDG + "13"]),
            OutcomeSpec("AffordableCleanEnergy", "More affordable clean energy",
                        "Members get renewable electricity at or below grid prices.", themes=[SDG + "7"]),
        ],
        indicators=[
            IndicatorSpec("TonnesGHGAvoided", "Tonnes of GHG emissions avoided",
                          "Tonnes of CO2-equivalent avoided compared with grid electricity.",
                          "Tonnes CO2e", UNIT["tonne"], ["ReducedGHGEmissions"],
                          annual_series(years, ["410", "455", "498", "540", "602", "655", "701"]),
                          themes=[SDG + "13"]),
            IndicatorSpec("RenewableMWh", "Renewable electricity generated",
                          "Megawatt-hours generated by the co-op's solar arrays.",
                          "MWh", UNIT["megawattHour"], ["AffordableCleanEnergy", "ReducedGHGEmissions"],
                          annual_series(years, ["1210", "1340", "1395", "1502", "1610", "1688", "1745"]),
                          themes=[SDG + "7", SDG + "13"]),
            IndicatorSpec("MembersServed", "Member households served",
                          "Households buying electricity through the co-op at year end.",
                          "Households", UNIT["countUnit"], ["AffordableCleanEnergy"],
                          annual_series(years, ["640", "702", "765", "810", "872", "915", "968"]),
                          themes=[SDG + "7"]),
        ],
        sectors=["Energy", "Climate"], provinces=["ON"], localities=["loc3", "loc4"],
        populations=["ps15", "ps25"], org_types=["Cooperative"],
        mgmt=(6, 3, [("edg3", 1), ("edg10", 2)]),
        board=(9, 5, [("edg4", 1), ("edg6", 1), ("edg10", 3)]),
        report_period=("2025", "2025-01-01T00:00:00-05:00", "2025-12-31T23:59:59-05:00"),
        profile_date="2026-02-27T00:00:00-05:00", team_date="2026-02-27T00:00:00-05:00",
    )


def northwind(years, profile_year=2025) -> OrgSpec:
    b = "https://northwind-food.example/"
    vals = {2019: ("820", "41000"), 2020: ("905", "52300"), 2021: ("960", "55100"), 2022: ("1040", "58900"),
            2023: ("1115", "61200"), 2024: ("1190", "64800"), 2025: ("1260", "67400")}
    return OrgSpec(
        base=b, slug="Northwind",
        legal_name="Northwind Food Recovery Society",
        street="88 Imaginary Avenue", city="Vancouver", region="BC", postal_code="V5K 0C3",
        business_number="345678912RC0001",
        contact=("Mika", "Tanaka", "mika.tanaka@northwind-food.example"),
        sdgs=[2, 12],
        outcomes=[
            OutcomeSpec("LessFoodWaste", "Less food waste sent to landfill",
                        "Surplus food is recovered instead of thrown away.", themes=[SDG + "12"]),
            OutcomeSpec("ImprovedFoodSecurity", "Improved food security",
                        "Low-income households have reliable access to healthy food.", themes=[SDG + "2"]),
        ],
        indicators=[
            IndicatorSpec("TonnesFoodRecovered", "Tonnes of food recovered",
                          "Tonnes of surplus food recovered from grocers and farms.",
                          "Tonnes", UNIT["tonne"], ["LessFoodWaste", "ImprovedFoodSecurity"],
                          annual_series(years, [vals[y][0] for y in years]), themes=[SDG + "12"]),
            IndicatorSpec("MealsProvided", "Meals provided",
                          "Meals provided through partner agencies.",
                          "Meals", UNIT["countUnit"], ["ImprovedFoodSecurity"],
                          annual_series(years, [vals[y][1] for y in years]), themes=[SDG + "2"]),
        ],
        sectors=["Agriculture", "Waste"], provinces=["BC"], localities=["loc1"],
        populations=["ps15", "ps14"], org_types=["Charitable"],
        mgmt=(5, 3, [("edg8", 2), ("edg10", 3)]),
        board=(8, 4, [("edg1", 1), ("edg10", 4)]),
        report_period=(str(profile_year), f"{profile_year}-01-01T00:00:00-08:00", f"{profile_year}-12-31T23:59:59-08:00"),
        profile_date=f"{profile_year + 1}-01-30T00:00:00-08:00", team_date=f"{profile_year + 1}-01-30T00:00:00-08:00",
    )


def maple_hollow(years, profile_year=2025) -> OrgSpec:
    b = "https://maplehollow-learning.example/"
    vals = {2019: ("210", "61"), 2020: ("188", "58"), 2021: ("236", "63"), 2022: ("251", "66"),
            2023: ("274", "68"), 2024: ("290", "71"), 2025: ("305", "73")}
    return OrgSpec(
        base=b, slug="MapleHollow",
        legal_name="Maple Hollow Learning Collective",
        street="7 Fictional Crescent", city="Winnipeg", region="MB", postal_code="R3C 0D4",
        business_number="456789123RC0001",
        contact=("Jordan", "Beaulieu", "jordan.beaulieu@maplehollow-learning.example"),
        sdgs=[4],
        outcomes=[OutcomeSpec("ImprovedAdultLiteracy", "Improved adult literacy",
                              "Adult learners gain the reading and writing skills they need for work and daily life.",
                              themes=[SDG + "4"])],
        indicators=[
            IndicatorSpec("LearnersEnrolled", "Adult learners enrolled",
                          "Adults enrolled in the literacy program during the year.",
                          "Learners", UNIT["countUnit"], ["ImprovedAdultLiteracy"],
                          annual_series(years, [vals[y][0] for y in years], tz="-06:00"), themes=[SDG + "4"]),
            IndicatorSpec("CompletionRate", "Program completion rate",
                          "Percent of enrolled learners who completed the program.",
                          "Percent", UNIT["percentUnit"], ["ImprovedAdultLiteracy"],
                          annual_series(years, [vals[y][1] for y in years], tz="-06:00"), themes=[SDG + "4"]),
        ],
        sectors=["Education"], provinces=["MB"], localities=["loc1"],
        populations=["ps20", "ps10"], org_types=["nonProfit"],
        mgmt=(3, 2, [("edg3", 1), ("edg10", 1)]),
        board=(6, 3, [("edg6", 1), ("edg10", 2)]),
        report_period=(str(profile_year), f"{profile_year}-01-01T00:00:00-06:00", f"{profile_year}-12-31T23:59:59-06:00"),
        profile_date=f"{profile_year + 1}-02-14T00:00:00-06:00", team_date=f"{profile_year + 1}-02-14T00:00:00-06:00",
    )


def prairie_spoke(years, profile_year=2025) -> OrgSpec:
    b = "https://prairiespoke-bikes.example/"
    vals = {2019: ("1450", "18"), 2020: ("1610", "21"), 2021: ("1720", "24"), 2022: ("1805", "26"),
            2023: ("1930", "29"), 2024: ("2040", "31"), 2025: ("2115", "33")}
    return OrgSpec(
        base=b, slug="PrairieSpoke",
        legal_name="Prairie Spoke Bicycle Works Ltd.",
        street="1200 Notional Street", city="Saskatoon", region="SK", postal_code="S7K 0E5",
        business_number="567891234RC0001",
        contact=("Alex", "Desjardins", "alex.desjardins@prairiespoke-bikes.example"),
        sdgs=[11, 8],
        outcomes=[
            OutcomeSpec("LowCarbonTransport", "More people using low-carbon transport",
                        "Refurbished bikes replace car trips.", themes=[SDG + "11"]),
            OutcomeSpec("SkilledTrades", "New skills for trade apprentices",
                        "Apprentices gain bicycle mechanic certification.", themes=[SDG + "8"]),
        ],
        indicators=[
            IndicatorSpec("BikesRefurbished", "Bicycles refurbished and sold",
                          "Refurbished bicycles sold or donated during the year.",
                          "Bicycles", UNIT["countUnit"], ["LowCarbonTransport"],
                          annual_series(years, [vals[y][0] for y in years], tz="-06:00"), themes=[SDG + "11"]),
            IndicatorSpec("ApprenticesCertified", "Apprentices certified",
                          "Apprentices who earned mechanic certification during the year.",
                          "Apprentices", UNIT["countUnit"], ["SkilledTrades"],
                          annual_series(years, [vals[y][1] for y in years], tz="-06:00"), themes=[SDG + "8"]),
        ],
        sectors=["Employment", "Climate"], provinces=["SK"], localities=["loc2"],
        populations=["ps24", "ps15"], org_types=["forProfit"],
        mgmt=(4, 1, [("edg5", 1)]),
        board=(5, 2, [("edg10", 2)]),
        report_period=(str(profile_year), f"{profile_year}-01-01T00:00:00-06:00", f"{profile_year}-12-31T23:59:59-06:00"),
        profile_date=f"{profile_year + 1}-03-02T00:00:00-06:00", team_date=f"{profile_year + 1}-03-02T00:00:00-06:00",
    )
