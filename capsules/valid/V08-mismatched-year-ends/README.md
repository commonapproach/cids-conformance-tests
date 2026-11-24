# V08-mismatched-year-ends: Organizations with different fiscal year ends

Two SFF organizations in one capsule: Silverbirch Family Services reports April-March, and Lakeshore Repair Café Co-operative reports July-June.

**Category:** Valid  
**Based on:** Gap listed in the 2025 sample set notes: "mismatched year ends".

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- Report periods that cross calendar years (e.g. 2023-04-01 to 2024-03-31).
- Two different fiscal calendars in one capsule.
- ReportInfo periods that match each organization's fiscal year.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- Report periods are kept exactly. They are not moved to calendar years or relabelled by the year they end in.
- Each organization keeps its own reports. Same-named periods (both have a `FY2024-25`) are not merged across organizations.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V08-mismatched-year-ends/capsule.jsonld
python -m cidsconformance dq capsules/valid/V08-mismatched-year-ends/capsule.jsonld
python -m cidsconformance compare capsules/valid/V08-mismatched-year-ends/capsule.jsonld your-export.jsonld
```
