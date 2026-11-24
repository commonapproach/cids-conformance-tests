# V09-bcorp-indicator-hascode: B Corp assessment as an Indicator with hasCode

Driftwood Outdoor Gear Inc. (SFF). The B Impact Assessment score is an Indicator with a `hasCode` link to a Code that identifies it as the standard B Impact score, plus five annual reports.

**Category:** Valid  
**Based on:** Gap listed in the 2025 sample set notes: "BCorp Assessments as Indicator + hasCode". In the Airtable samples the B Corp reports had no Indicator at all.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- `cids:hasCode` on an Indicator, pointing to a `cids:Code` with `definedBy` and `schema:codeValue`.
- A standards organization typed as both `cids:StandardsOrganization` and `cids:Organization`.
- Decimal scores in `hasNumericalValue` with `cids:scoreUnit`.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- The Indicator keeps its `hasCode` link, and the Code node comes back with all its properties.
- Every B Impact report stays linked to the Indicator with `forIndicator`.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V09-bcorp-indicator-hascode/capsule.jsonld
python -m cidsconformance dq capsules/valid/V09-bcorp-indicator-hascode/capsule.jsonld
python -m cidsconformance compare capsules/valid/V09-bcorp-indicator-hascode/capsule.jsonld your-export.jsonld
```
