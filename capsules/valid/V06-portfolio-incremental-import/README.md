# V06-portfolio-incremental-import: Three organizations, imported in two steps

A three-organization portfolio. Part 1 has every year up to 2024, part 2 has only 2025. Importing both must give the same result as importing the merged file.

**Category:** Valid  
**Based on:** 2025 sample set notes: "preload Multiple Orgs for all years up to 2024, then import Multiple Orgs only recent years". Rebuilt with fictional organizations.

## Files

- `part-1-up-to-2024.jsonld`: the capsule in JSON-LD. Reports for 2019-2024; 2024 SFF profiles. `part-1-up-to-2024.ttl` has the same data in Turtle.
- `part-2-2025.jsonld`: the capsule in JSON-LD. Reports for 2025 only; 2025 SFF profiles. `part-2-2025.ttl` has the same data in Turtle.
- `expected-after-both-parts.jsonld`: the capsule in JSON-LD. Part 1 and part 2 merged. `expected-after-both-parts.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- Several organizations in one capsule.
- Adding a new year to data that is already loaded: same Organization, Outcome and Indicator IRIs, new IndicatorReports and new dated SFF profiles.
- Indicators whose `hasIndicatorReport` list grows between imports.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- Import `part-1-up-to-2024.jsonld`, then export. The export must match part 1.
- Then import `part-2-2025.jsonld` on top, and export again. The export must match `expected-after-both-parts.jsonld`: nothing from part 1 is lost or duplicated, and the 2025 data is added.
- Shared nodes (Organizations, Outcomes, Indicators, Addresses) are updated in place, not created again under a new IRI.

## Expected validation result

### `part-1-up-to-2024.jsonld`

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

### `part-2-2025.jsonld`

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

### `expected-after-both-parts.jsonld`

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V06-portfolio-incremental-import/part-1-up-to-2024.jsonld
python -m cidsconformance dq capsules/valid/V06-portfolio-incremental-import/part-1-up-to-2024.jsonld
python -m cidsconformance compare capsules/valid/V06-portfolio-incremental-import/part-1-up-to-2024.jsonld your-export.jsonld
```
