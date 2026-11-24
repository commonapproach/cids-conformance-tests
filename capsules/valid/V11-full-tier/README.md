# V11-full-tier: Full, realistic Full tier capsule

Cedarline Home Retrofit Co-operative (SFF): a complete impact model, with a program, service, activities, inputs, outputs, beneficial and contributing stakeholders, a counterfactual, an impact risk and a stakeholder report, as well as Outcomes, Indicators, reports and targets.

**Category:** Valid  
**Based on:** New. The 2025 sample set is all Basic tier or SFF; the updated ticket asks for a Full tier capsule.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- ImpactPathway (also typed ImpactModel), Program, Service, three Activities, an Input with planned and actual amounts and a Resource type, an Output.
- BeneficialStakeholder and ContributingStakeholder (each also typed Stakeholder), with `benefitsFrom`, `cids:contributes` and `cids:performs`.
- StakeholderOutcome with `fromPerspectiveOf`, `hasImportance` and `intendedImpact`.
- ImpactReport with scale, depth and duration, `hasExpectation`, `hasReportedImpact` and an EvidenceRisk (also typed ImpactRisk); a Counterfactual.
- Indicators with `hasThreshold`, `hasIdentifier`, `hasAccess` and `prov:wasGeneratedBy`.
- StakeholderReport with a CharacteristicReport.
- `sch:dateCreated` and `description` on every CIDS node, and the SFF profile nodes (OrganizationProfile, TeamProfiles, EDGProfiles, FundingStatus, ReportInfo).
- Also passes the Essential tier shapes.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- These properties are written as prefixed keys, because the CIDS/SFF contexts have no term for them (or, for `cids:hasComment`, the SFF term means something else). They must all come back: `cids:beneficialSizeEnd`, `cids:beneficialSizeStart`, `cids:contributes`, `cids:forImpactReport`, `cids:forIndicatorReport`, `cids:forTarget`, `cids:hasActualAmount`, `cids:hasComment`, `cids:hasConsequence`, `cids:hasContributingStakeholder`, `cids:hasLikelihood`, `cids:hasPlannedAmount`, `cids:hasTarget`, `cids:hasType`, `cids:inputFor`, `cids:performs`, `i72:numberOf`, `oep:partOf`, `prov:wasGeneratedBy`, `sch:codeValue`, `sch:dateCreated`. An importer that only maps context terms will drop them silently.
- `cids:hasComment` stays `cids:hasComment`. It must not turn into `sff:hasComment` (the SFF context maps the short key `hasComment` to `sff:hasComment`).
- Measures keep their IRIs. They are not turned into blank nodes or nested copies (the Essential tier requires `i72:value` to point at an IRI).
- `isUnderserved` stays an `xsd:boolean`, and enumerated values such as `hasCatchmentArea: "local"` keep their exact text.
- Nodes with two types (`cids:BeneficialStakeholder` + `cids:Stakeholder`, `cids:EvidenceRisk` + `cids:ImpactRisk`, `cids:ImpactPathway` + `cids:ImpactModel`) keep both types.
- `cids:beneficialSizeStart` / `cids:beneficialSizeEnd` stay `xsd:positiveInteger`.
- "Homes retrofitted" comes back as one Indicator with both `forOutcome` links.

## Expected validation result

Passes Basic tier, SFF, Essential tier and Full tier SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

The published Essential and Full tier shapes have bugs that make every capsule fail. The tools correct them when loading the shapes; see [reference/SOURCES.md](../../../reference/SOURCES.md#corrections-to-the-published-shapes).

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V11-full-tier/capsule.jsonld --profile basic --profile sff --profile essential --profile full
python -m cidsconformance dq capsules/valid/V11-full-tier/capsule.jsonld
python -m cidsconformance compare capsules/valid/V11-full-tier/capsule.jsonld your-export.jsonld
```
