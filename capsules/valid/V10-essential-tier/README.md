# V10-essential-tier: Full, realistic Essential tier capsule

Harbourlight Community Kitchen Society: a training kitchen with two Outcomes, two Indicators (one linked to both Outcomes) and three years of reports, with everything the Essential tier asks for: targets, baselines, stakeholders, stakeholder outcomes and impact reports.

**Category:** Valid  
**Based on:** New. The 2025 sample set is all Basic tier or SFF; the updated ticket asks for an Essential tier capsule.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- The core Essential tier classes: Organization, Address, Outcome, Indicator, IndicatorReport, Target, Theme, Code, StandardsOrganization, Stakeholder, Characteristic, StakeholderOutcome, ImpactReport, ImpactScale, ImpactDepth, ImpactDuration, Measure. (BeneficialStakeholder, ContributingStakeholder and ImpactPathway are in V11.)
- Indicators with `definedBy` (the organization itself, or a standards body), `hasBaseline` and `cids:hasTarget`.
- Each IndicatorReport points to that year's Target with `cids:forTarget`, and the Target points back.
- A Code with `hasSpecification` (`xsd:anyURI`), `sch:codeValue` and a value.
- Measures with their own IRIs instead of blank nodes.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- These properties are written as prefixed keys, because the CIDS/SFF contexts have no term for them (or, for `cids:hasComment`, the SFF term means something else). They must all come back: `cids:forIndicatorReport`, `cids:forTarget`, `cids:hasComment`, `cids:hasTarget`, `sch:codeValue`, `sch:dateCreated`. An importer that only maps context terms will drop them silently.
- `cids:hasComment` stays `cids:hasComment`. It must not turn into `sff:hasComment` (the SFF context maps the short key `hasComment` to `sff:hasComment`).
- Measures keep their IRIs. They are not turned into blank nodes or nested copies (the Essential tier requires `i72:value` to point at an IRI).
- `isUnderserved` stays an `xsd:boolean`, and enumerated values such as `hasCatchmentArea: "local"` keep their exact text.
- "Community meals served" comes back as one Indicator with both `forOutcome` links.

## Expected validation result

Passes Basic tier, SFF and Essential tier SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

The published Essential and Full tier shapes have bugs that make every capsule fail. The tools correct them when loading the shapes; see [reference/SOURCES.md](../../../reference/SOURCES.md#corrections-to-the-published-shapes).

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V10-essential-tier/capsule.jsonld --profile basic --profile sff --profile essential
python -m cidsconformance dq capsules/valid/V10-essential-tier/capsule.jsonld
python -m cidsconformance compare capsules/valid/V10-essential-tier/capsule.jsonld your-export.jsonld
```
