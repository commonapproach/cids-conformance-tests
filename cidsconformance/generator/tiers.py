"""Nodes for the Essential tier and Full tier capsules (V10, V11).

Both start from an ordinary organization built by ``world.build_org`` and add
what the Essential and Full tier shapes require. Many of those properties
have no term in the published JSON-LD contexts (``forTarget``,
``dateCreated``, ``partOf``, ``wasGeneratedBy`` ...), so they are written as
prefixed keys such as ``"cids:forTarget"``, which any JSON-LD processor
expands using the prefixes the contexts do define.
"""

from __future__ import annotations

from .common import UNIT, find, node
from .world import IndicatorSpec, OrgSpec, OutcomeSpec, SDG, annual_series, build_org


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def ref(*iris: str):
    """A link written with a prefixed key, e.g. {"cids:forTarget": ref(x)}."""
    refs = [{"@id": i} for i in iris]
    return refs[0] if len(refs) == 1 else refs


def dt(value: str) -> dict:
    return {"@value": value, "@type": "xsd:dateTime"}


def positive_int(value: int) -> dict:
    return {"@value": str(value), "@type": "xsd:positiveInteger"}


def measure_node(iri: str, value: str, unit: str | None = None) -> dict:
    m = node("i72:Measure", iri, hasNumericalValue=value)
    if unit:
        m["unit_of_measure"] = unit
    return m


def lift_measures(nodes: list[dict]) -> list[dict]:
    """Give every embedded Measure its own IRI and make it a top-level node.

    The Essential tier requires ``i72:value`` to point at an IRI, not a
    blank node. Each Measure is named after the node and property that hold
    it, e.g. ``.../IndicatorReport/MealsServed/2024/value/``."""
    out = []
    for n in nodes:
        out.append(n)
        for key, val in list(n.items()):
            if isinstance(val, dict) and val.get("@type") == "i72:Measure" and "@id" not in val:
                iri = f"{n['@id'].rstrip('/')}/{key.split(':')[-1]}/"
                out.append(measure_node(iri, val["hasNumericalValue"], val.get("unit_of_measure")))
                # Context terms such as "value" are declared as links; a
                # prefixed key ("cids:hasActualAmount") needs an explicit @id.
                n[key] = {"@id": iri} if ":" in key else iri
    return out


def add(n: dict, **props) -> dict:
    """Add properties to a node; keys with a colon go in via a dict."""
    n.update({k: v for k, v in props.items() if v is not None})
    return n


# --------------------------------------------------------------------------
# V10: Essential tier
# --------------------------------------------------------------------------

STANDARDS_BODY = "https://impact-standards-council.example/Organization/ISC/"


def harbourlight() -> OrgSpec:
    years = [2023, 2024, 2025]
    return OrgSpec(
        base="https://harbourlight-kitchens.example/", slug="Harbourlight",
        legal_name="Harbourlight Community Kitchen Society",
        street="52 Specimen Wharf Road", city="Halifax", region="NS", postal_code="B3K 0F7",
        business_number="678912345RC0001",
        contact=("Casey", "MacIsaac", "casey.macisaac@harbourlight-kitchens.example"),
        sdgs=[2, 8],
        outcomes=[
            OutcomeSpec("GraduatesInFoodServiceJobs", "Graduates in stable food-service jobs",
                        "People who complete the kitchen training program find and keep jobs in food service.",
                        themes=[SDG + "8"]),
            OutcomeSpec("ImprovedFoodSecurity", "Improved food security for neighbours",
                        "Households in the neighbourhood have reliable access to healthy meals.",
                        themes=[SDG + "2"]),
        ],
        indicators=[
            IndicatorSpec("GraduatesEmployed", "Graduates employed after six months",
                          "Program graduates who are working in food service six months after finishing the program.",
                          "Graduates", UNIT["countUnit"], ["GraduatesInFoodServiceJobs"],
                          annual_series(years, ["38", "44", "51"], tz="-04:00"), themes=[SDG + "8"]),
            IndicatorSpec("MealsServed", "Community meals served",
                          "Meals cooked by trainees and served at the community dining room or delivered to households.",
                          "Meals", UNIT["countUnit"], ["ImprovedFoodSecurity", "GraduatesInFoodServiceJobs"],
                          annual_series(years, ["21400", "23850", "26100"], tz="-04:00"), themes=[SDG + "2", SDG + "8"]),
        ],
        sff=False,
    )


def essential_tier_nodes() -> list[dict]:
    o = harbourlight()
    nodes = build_org(o)
    org = find(nodes, o.org)
    b = o.base

    # A fictional standards body defines one of the indicators and a Code.
    code = f"{b}Code/FoodServiceCertificate/"
    nodes.append(node(["cids:StandardsOrganization", "cids:Organization"], STANDARDS_BODY,
                      hasLegalName="Impact Standards Council (fictional)"))
    nodes.append(node(
        "cids:Code", code,
        hasName="Recognised food-service training credential",
        hasDescription="Identifies indicators about graduates of a recognised food-service training program.",
        hasSpecification="https://impact-standards-council.example/codes/food-service-credential",
        definedBy=STANDARDS_BODY,
        value=f"{code.rstrip('/')}/value/",
        **{"sch:codeValue": "FSC-01"},
    ))
    nodes.append(measure_node(f"{code.rstrip('/')}/value/", "1", UNIT["unspecifiedUnit"]))

    # Indicators: definedBy, baseline, targets, and one Code.
    baselines = {"GraduatesEmployed": "30", "MealsServed": "18000"}
    targets = {"GraduatesEmployed": ["40", "45", "50"], "MealsServed": ["22000", "24000", "26000"]}
    for spec in o.indicators:
        ind = find(nodes, o.indicator(spec.slug))
        target_iris = [f"{b}Target/{spec.slug}/{p}/" for p, *_ in spec.series]
        add(ind,
            definedBy=STANDARDS_BODY if spec.slug == "GraduatesEmployed" else o.org,
            hasBaseline={"@type": "i72:Measure", "hasNumericalValue": baselines[spec.slug],
                         "unit_of_measure": spec.unit},
            hasCode=[code] if spec.slug == "GraduatesEmployed" else None,
            **{"cids:hasTarget": ref(*target_iris)})
        for (period, start, end, _value), target, goal in zip(spec.series, target_iris, targets[spec.slug]):
            report = o.report(spec.slug, period)
            add(find(nodes, report), **{"cids:forTarget": ref(target)})
            nodes.append(node(
                "cids:Target", target,
                hasName=f"{spec.name} target {period}",
                value={"@type": "i72:Measure", "hasNumericalValue": goal, "unit_of_measure": spec.unit},
                startedAtTime=start, endedAtTime=end,
                **{"cids:hasComment": f"Board-approved target for {period}.",
                   "sch:dateCreated": dt(f"{int(period) - 1}-11-15T09:00:00-04:00"),
                   "cids:forIndicatorReport": ref(report)},
            ))

    # Stakeholders and what each Outcome means for them.
    participants = f"{b}Stakeholder/TrainingParticipants/"
    neighbours = f"{b}Stakeholder/NeighbourhoodHouseholds/"
    barriers = f"{b}Characteristic/BarriersToEmployment/"
    low_income = f"{b}Characteristic/LowIncomeHousehold/"
    nodes += [
        node("cids:Stakeholder", participants, hasName="Kitchen training participants",
             hasDescription="Adults facing barriers to employment who enrol in the 16-week kitchen training program.",
             forOrganization=o.org, hasCatchmentArea="local", hasCharacteristic=[barriers]),
        node("cids:Stakeholder", neighbours, hasName="Neighbourhood households",
             hasDescription="Low-income households in the north end who eat at the dining room or get meals delivered.",
             forOrganization=o.org, hasCatchmentArea="local", hasCharacteristic=[low_income]),
        node("cids:Characteristic", barriers, hasName="Facing barriers to employment"),
        node("cids:Characteristic", low_income, hasName="Low-income household"),
    ]
    so_jobs = f"{b}StakeholderOutcome/TrainingParticipants/GraduatesInFoodServiceJobs/"
    so_food = f"{b}StakeholderOutcome/NeighbourhoodHouseholds/ImprovedFoodSecurity/"
    nodes += [
        node("cids:StakeholderOutcome", so_jobs, hasName="Stable jobs for training participants",
             hasDescription="Participants move from unemployment or precarious work into steady food-service jobs.",
             forOutcome=o.outcome("GraduatesInFoodServiceJobs"), forStakeholder=participants, isUnderserved=True),
        node("cids:StakeholderOutcome", so_food, hasName="Reliable meals for neighbourhood households",
             hasDescription="Households that often skip meals get at least one healthy meal a day.",
             forOutcome=o.outcome("ImprovedFoodSecurity"), forStakeholder=neighbours, isUnderserved=False),
    ]

    # One ImpactReport per Outcome for 2025, with scale, depth and duration.
    start, end = "2025-01-01T00:00:00-04:00", "2025-12-31T23:59:59-04:00"
    for oc_slug, so, label, scale, depth, duration, ind_slug in (
        ("GraduatesInFoodServiceJobs", so_jobs, "jobs", "51", "62", "18", "GraduatesEmployed"),
        ("ImprovedFoodSecurity", so_food, "food security", "26100", "40", "12", "MealsServed"),
    ):
        ir = f"{b}ImpactReport/{oc_slug}/2025/"
        parts = {
            "ImpactScale": ("cids:ImpactScale", f"How many: {scale} people or meals reached in 2025.", scale, UNIT["countUnit"]),
            "ImpactDepth": ("cids:ImpactDepth", f"How much: {depth}% reported a large improvement.", depth, UNIT["percentUnit"]),
            "ImpactDuration": ("cids:ImpactDuration", f"How long: the change lasts about {duration} months.", duration, None),
        }
        for kind, (cls, desc, val, unit) in parts.items():
            nodes.append(node(cls, f"{ir}{kind}/", hasDescription=desc,
                              value={"@type": "i72:Measure", "hasNumericalValue": val, "unit_of_measure": unit or UNIT["unspecifiedUnit"]},
                              forIndicator=o.indicator(ind_slug)))
        nodes.append(node(
            "cids:ImpactReport", ir,
            hasName=f"Impact report 2025: {label}",
            forOrganization=o.org, forOutcome=o.outcome(oc_slug),
            hasImpactScale=f"{ir}ImpactScale/", hasImpactDepth=f"{ir}ImpactDepth/",
            hasImpactDuration=f"{ir}ImpactDuration/",
            startedAtTime=start, endedAtTime=end,
            **{"cids:hasComment": "Based on the year-end participant survey and the meal log."},
        ))
        add(find(nodes, o.outcome(oc_slug)), hasStakeholderOutcome=[so], hasImpactReport=[ir])
        add(find(nodes, so), hasImpactReport=[ir])

    add(org, hasStakeholder=[participants, neighbours])
    return lift_measures(nodes)


# --------------------------------------------------------------------------
# V11: Full tier
# --------------------------------------------------------------------------

def cedarline() -> OrgSpec:
    years = [2024, 2025]
    return OrgSpec(
        base="https://cedarline-retrofit.example/", slug="Cedarline",
        legal_name="Cedarline Home Retrofit Co-operative",
        street="300 Illustrative Street", city="Thunder Bay", region="ON", postal_code="P7B 0G8",
        business_number="789123456RC0001",
        contact=("Riley", "Wapoose", "riley.wapoose@cedarline-retrofit.example"),
        sdgs=[7, 8],
        outcomes=[
            OutcomeSpec("LowerEnergyBills", "Lower home energy bills",
                        "Low-income homeowners spend less of their income on heating and electricity.",
                        themes=[SDG + "7"]),
            OutcomeSpec("YouthInSkilledTrades", "Youth working in skilled trades",
                        "Young people who train on retrofit crews go on to apprenticeships and trades jobs.",
                        themes=[SDG + "8"]),
        ],
        indicators=[
            IndicatorSpec("HomesRetrofitted", "Homes retrofitted",
                          "Homes where the crew finished insulation, air sealing and a heat-pump install.",
                          "Homes", UNIT["countUnit"], ["LowerEnergyBills", "YouthInSkilledTrades"],
                          annual_series(years, ["64", "79"]), themes=[SDG + "7", SDG + "8"]),
            IndicatorSpec("AverageBillSavings", "Average yearly energy bill savings",
                          "Average drop in a retrofitted household's yearly energy bill, in Canadian dollars.",
                          "CAD per household per year", UNIT["cad"], ["LowerEnergyBills"],
                          annual_series(years, ["1180.00", "1265.50"]), themes=[SDG + "7"]),
        ],
        sectors=["Energy"], provinces=["ON"], localities=["loc2"],
        populations=["ps15"], org_types=["Cooperative"],
        mgmt=(5, 3, [("edg3", 2), ("edg10", 1)]),
        board=(7, 4, [("edg3", 2), ("edg6", 1), ("edg10", 1)]),
        report_period=("2025", "2025-01-01T00:00:00-05:00", "2025-12-31T23:59:59-05:00"),
        profile_date="2026-02-20T00:00:00-05:00", team_date="2026-02-20T00:00:00-05:00",
    )


CREATED = "2026-01-12T09:30:00-05:00"


def full_tier_nodes() -> list[dict]:
    o = cedarline()
    nodes = build_org(o)
    b = o.base
    org = find(nodes, o.org)
    start24, end24 = annual_series([2024], ["0"])[0][1:3]
    start25, end25 = annual_series([2025], ["0"])[0][1:3]

    model = f"{b}ImpactPathway/Retrofit/"
    program = f"{b}Program/RetrofitCrew/"
    service = f"{b}Service/HomeRetrofit/"
    act_train = f"{b}Activity/CrewTraining/"
    act_retrofit = f"{b}Activity/HomeRetrofits/"
    act_survey = f"{b}Activity/HouseholdSurvey/"
    inp = f"{b}Input/RetrofitMaterials/"
    resource = f"{b}Resource/InsulationAndHeatPumps/"
    output = f"{b}Output/CompletedRetrofits/"
    homeowners = f"{b}Stakeholder/Homeowners/"
    trainees = f"{b}Stakeholder/YouthTrainees/"
    tradespeople = f"{b}Stakeholder/VolunteerTradespeople/"
    ch_income = f"{b}Characteristic/LowIncomeHomeowner/"
    ch_youth = f"{b}Characteristic/Aged18To29/"
    code = f"{b}Code/DeepRetrofit/"
    contact = o.iri("Person", f"{o.slug}Contact")

    nodes += [
        node(["cids:ImpactPathway", "cids:ImpactModel"], model, hasName="Retrofit impact pathway",
             hasDescription="How crew training and home retrofits lead to lower bills and trades careers.",
             forOrganization=o.org, hasActivity=[act_train, act_retrofit, act_survey], hasProgram=[program],
             hasOutcome=[o.outcome(x.slug) for x in o.outcomes],
             hasIndicator=[o.indicator(x.slug) for x in o.indicators], hasInput=[inp], hasOutput=[output]),
        node("cids:Program", program, hasName="Youth retrofit crew program",
             hasDescription="A paid, year-long program in which youth crews retrofit low-income homes.",
             hasService=[service], hasOutcome=[o.outcome(x.slug) for x in o.outcomes],
             hasBeneficialStakeholder=[homeowners, trainees], hasContributingStakeholder=[tradespeople],
             hasInput=[inp], hasOutput=[output], **{"oep:partOf": ref(model)}),
        node("cids:Service", service, hasName="Free home energy retrofit",
             hasDescription="Insulation, air sealing and a heat pump at no cost to eligible homeowners.",
             startedAtTime=start25, endedAtTime=end25, canProduce=[o.outcome("LowerEnergyBills")],
             **{"cids:beneficialSizeStart": positive_int(1), "cids:beneficialSizeEnd": positive_int(6),
                "oep:partOf": ref(model)}),
        node("cids:Activity", act_train, hasName="Crew training",
             hasDescription="Classroom and on-site training in building science and safe work.",
             canProduce=[o.outcome("YouthInSkilledTrades")], **{"oep:partOf": ref(model)}),
        node("cids:Activity", act_retrofit, hasName="Home retrofits",
             hasDescription="Crews retrofit homes under the supervision of licensed tradespeople.",
             hasInput=[inp], hasOutput=[output], canProduce=[o.outcome("LowerEnergyBills")],
             **{"oep:partOf": ref(model)}),
        node("cids:Activity", act_survey, hasName="Household survey and bill tracking",
             hasDescription="Homeowners share 12 months of bills before and after the retrofit.",
             **{"oep:partOf": ref(model)}),
        node("act:Resource", resource, hasName="Insulation and heat pumps"),
        node("cids:Input", inp, hasName="Retrofit materials",
             hasDescription="Insulation, air-sealing supplies and heat pumps bought for the year.",
             startedAtTime=start25, endedAtTime=end25,
             **{"cids:hasType": ref(resource),
                "cids:hasPlannedAmount": {"@type": "i72:Measure", "hasNumericalValue": "640000", "unit_of_measure": UNIT["cad"]},
                "cids:hasActualAmount": {"@type": "i72:Measure", "hasNumericalValue": "612450.75", "unit_of_measure": UNIT["cad"]},
                "cids:inputFor": ref(act_retrofit), "cids:hasContributingStakeholder": ref(tradespeople),
                "oep:partOf": ref(model)}),
        node("cids:Output", output, hasName="Completed retrofits",
             hasDescription="Homes signed off by a licensed inspector.",
             canProduce=[o.outcome("LowerEnergyBills")], usedByIndicator=[o.indicator("HomesRetrofitted")],
             **{"oep:partOf": ref(model)}),
        node(["cids:BeneficialStakeholder", "cids:Stakeholder"], homeowners, hasName="Low-income homeowners",
             hasDescription="Homeowners in the city whose household income is below the program limit.",
             forOrganization=o.org, hasCatchmentArea="local", hasCharacteristic=[ch_income],
             benefitsFrom=[o.outcome("LowerEnergyBills")], **{"oep:partOf": ref(model)}),
        node(["cids:BeneficialStakeholder", "cids:Stakeholder"], trainees, hasName="Youth trainees",
             hasDescription="Young adults hired onto retrofit crews for one year.",
             forOrganization=o.org, hasCatchmentArea="provincial", hasCharacteristic=[ch_youth],
             benefitsFrom=[o.outcome("YouthInSkilledTrades")], **{"oep:partOf": ref(model)}),
        node(["cids:ContributingStakeholder", "cids:Stakeholder"], tradespeople, hasName="Volunteer tradespeople",
             hasDescription="Retired and working tradespeople who supervise crews.",
             forOrganization=o.org, hasCatchmentArea="local",
             **{"cids:contributes": ref(inp), "cids:performs": ref(act_train), "oep:partOf": ref(model)}),
        node("cids:Characteristic", ch_income, hasName="Low-income homeowner", forStakeholder=[homeowners]),
        node("cids:Characteristic", ch_youth, hasName="Aged 18 to 29", forStakeholder=[trainees]),
        node(["cids:StandardsOrganization", "cids:Organization"], STANDARDS_BODY,
             hasLegalName="Impact Standards Council (fictional)",
             hasDescription="A fictional body that publishes impact codes, used only in this test suite."),
        node("cids:Code", code, hasName="Deep energy retrofit",
             hasDescription="Identifies indicators about retrofits that cut a home's energy use by at least half.",
             hasSpecification="https://impact-standards-council.example/codes/deep-retrofit",
             definedBy=STANDARDS_BODY, value=f"{code.rstrip('/')}/value/",
             **{"sch:codeValue": "DER-50"}),
        measure_node(f"{code.rstrip('/')}/value/", "50", UNIT["percentUnit"]),
    ]

    # Outcomes, Indicators, reports and targets.
    for oc in o.outcomes:
        add(find(nodes, o.outcome(oc.slug)), canEnable=None, **{"oep:partOf": ref(model)})
    thresholds = {"HomesRetrofitted": "40", "AverageBillSavings": "800.00"}
    baselines = {"HomesRetrofitted": "0", "AverageBillSavings": "0.00"}
    goals = {"HomesRetrofitted": ["60", "75"], "AverageBillSavings": ["1100.00", "1200.00"]}
    for n_ind, spec in enumerate(o.indicators, start=1):
        ind = find(nodes, o.indicator(spec.slug))
        target_iris = [f"{b}Target/{spec.slug}/{p}/" for p, *_ in spec.series]
        add(ind,
            definedBy=o.org, hasIdentifier=f"CED-IND-{n_ind:02d}",
            hasBaseline={"@type": "i72:Measure", "hasNumericalValue": baselines[spec.slug], "unit_of_measure": spec.unit},
            hasThreshold={"@type": "i72:Measure", "hasNumericalValue": thresholds[spec.slug], "unit_of_measure": spec.unit},
            hasCode=[code] if spec.slug == "HomesRetrofitted" else None,
            hasAccess=[homeowners],
            **{"prov:wasGeneratedBy": ref(act_retrofit if spec.slug == "HomesRetrofitted" else act_survey),
               "cids:hasTarget": ref(*target_iris)})
        for (period, start, end, _v), target, goal in zip(spec.series, target_iris, goals[spec.slug]):
            report = o.report(spec.slug, period)
            add(find(nodes, report), forStakeholder=homeowners,
                **{"cids:forTarget": ref(target),
                   "prov:wasGeneratedBy": ref(act_retrofit if spec.slug == "HomesRetrofitted" else act_survey),
                   "cids:hasComment": f"Checked against the {period} inspection log."})
            nodes.append(node(
                "cids:Target", target, hasName=f"{spec.name} target {period}",
                value={"@type": "i72:Measure", "hasNumericalValue": goal, "unit_of_measure": spec.unit},
                startedAtTime=start, endedAtTime=end,
                **{"cids:hasComment": f"Target set in the {period} funding agreement.",
                   "sch:dateCreated": dt(f"{int(period) - 1}-12-01T09:00:00-05:00"),
                   "cids:forIndicatorReport": ref(report)}))

    # Stakeholder outcomes, impact report, counterfactual and risk.
    so = f"{b}StakeholderOutcome/Homeowners/LowerEnergyBills/"
    ir = f"{b}ImpactReport/LowerEnergyBills/2025/"
    cf = f"{b}Counterfactual/BillsWithoutRetrofit/2025/"
    risk = f"{b}ImpactRisk/SurveyResponseRate/"
    nodes += [
        node("cids:StakeholderOutcome", so, hasName="Lower bills for low-income homeowners",
             hasDescription="Homeowners keep more of their income because heating costs less.",
             forOutcome=o.outcome("LowerEnergyBills"), forStakeholder=homeowners, fromPerspectiveOf=homeowners,
             hasImportance="highImportance", intendedImpact="positive", isUnderserved=True,
             hasIndicator=[o.indicator("AverageBillSavings")], hasImpactReport=[ir]),
        node("cids:Counterfactual", cf, hasDescription="Expected bills had the homes not been retrofitted, from utility rate trends.",
             value={"@type": "i72:Measure", "hasNumericalValue": "0.00", "unit_of_measure": UNIT["cad"]},
             startedAtTime=start25, endedAtTime=end25, **{"prov:wasGeneratedBy": ref(act_survey)}),
        node(["cids:EvidenceRisk", "cids:ImpactRisk"], risk, hasIdentifier="CED-RISK-01",
             hasDescription="Fewer than half of homeowners may return the 12-month bill survey.",
             hasMitigation=["Collect bills directly from the utility with the homeowner's consent."],
             forOutcome=[o.outcome("LowerEnergyBills")],
             **{"cids:hasLikelihood": "likely", "cids:hasConsequence": "average", "cids:forImpactReport": ref(ir)}),
    ]
    for kind, cls, desc, val, unit, extra in (
        ("ImpactScale", "cids:ImpactScale", "How many: 79 households had lower bills in 2025.", "79", UNIT["countUnit"], {}),
        ("ImpactDepth", "cids:ImpactDepth", "How much: bills fell by 41% on average.", "41", UNIT["percentUnit"], {}),
        ("ImpactDuration", "cids:ImpactDuration", "How long: savings last for the 20-year life of the equipment.", "20", UNIT["unspecifiedUnit"],
         {"startedAtTime": start25, "endedAtTime": "2045-12-31T23:59:59-05:00"}),
    ):
        nodes.append(node(cls, f"{ir}{kind}/", hasDescription=desc,
                          value={"@type": "i72:Measure", "hasNumericalValue": val, "unit_of_measure": unit},
                          forIndicator=o.indicator("AverageBillSavings"), hasCounterfactual=[cf] if kind == "ImpactDepth" else None,
                          **extra))
    nodes.append(node(
        "cids:ImpactReport", ir, hasName="Impact report 2025: lower energy bills",
        forOrganization=o.org, forOutcome=o.outcome("LowerEnergyBills"),
        hasImpactScale=f"{ir}ImpactScale/", hasImpactDepth=f"{ir}ImpactDepth/", hasImpactDuration=f"{ir}ImpactDuration/",
        hasExpectation="Savings were expected to reach CAD 1,200 per household; actual savings beat that.",
        hasReportedImpact="positive", hasImpactRisk=[risk],
        startedAtTime=start25, endedAtTime=end25,
        **{"cids:hasComment": "Savings are measured from 12 months of bills before and after each retrofit."}))
    add(find(nodes, o.outcome("LowerEnergyBills")), hasStakeholderOutcome=[so], hasImpactReport=[ir])

    # Stakeholder report with a characteristic breakdown.
    sr = f"{b}StakeholderReport/Homeowners/2025/"
    cr = f"{b}CharacteristicReport/Homeowners/2025/LowIncome/"
    nodes += [
        node("cids:StakeholderReport", sr, forOrganization=[o.org], forStakeholder=[homeowners],
             hasCharacteristicReport=[cr], startedAtTime=start25, endedAtTime=end25),
        node("cids:CharacteristicReport", cr, forCharacteristic=[ch_income],
             **{"i72:numberOf": {"@type": "i72:Measure", "hasNumericalValue": "79", "unit_of_measure": UNIT["countUnit"]}}),
    ]

    add(org, hasDescription="A worker co-operative that trains youth crews to retrofit low-income homes.",
        hasPurpose=["Cut energy poverty and open trades careers for young people in northwestern Ontario."],
        hasWebAddress=["https://cedarline-retrofit.example/"],
        hasContact=[contact], hasProgram=[program], hasStakeholder=[homeowners, trainees, tradespeople])

    # Every CIDS node in the Full tier carries a creation date and a
    # schema.org description (Info-level in the shapes).
    nodes = lift_measures(nodes)
    for n in nodes:
        types = n["@type"] if isinstance(n["@type"], list) else [n["@type"]]
        is_cids = any(t.startswith("cids:") for t in types)
        is_ours = n["@id"].startswith(b) or n["@id"] == STANDARDS_BODY   # not codelist nodes
        if not (is_cids and is_ours):
            continue
        n.setdefault("sch:dateCreated", dt(CREATED))
        n.setdefault("description", _summary(n))
    return nodes


def _summary(n: dict) -> str:
    types = n["@type"] if isinstance(n["@type"], list) else [n["@type"]]
    label = n.get("hasName") or n.get("hasLegalName") or n.get("streetAddress") or n["@id"].rstrip("/").split("/")[-1]
    return f"{types[0].split(':')[-1]}: {label}"
