# V07-quarterly-reporting: A portfolio organization that reports by quarter

Harbourlight Health Navigation Inc. (SFF). One Indicator has seven quarterly reports (2024-Q1 to 2025-Q3), another has annual reports, and the ReportInfo covers one quarter.

**Category:** Valid  
**Based on:** Gap listed in the 2025 sample set notes: "portfolio organizations that report by quarter".

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- Quarterly `startedAtTime`/`endedAtTime` periods next to annual ones in the same capsule.
- UTC offsets that change at daylight-saving time (-04:00 in winter, -03:00 in summer).
- A ReportInfo for a quarter, not a year.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- Each quarterly report keeps its own start and end. Reports are not merged into years and periods are not snapped to calendar years.
- UTC offsets are preserved as written (strict mode), or at least the same instant is kept (default mode).

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V07-quarterly-reporting/capsule.jsonld
python -m cidsconformance dq capsules/valid/V07-quarterly-reporting/capsule.jsonld
python -m cidsconformance compare capsules/valid/V07-quarterly-reporting/capsule.jsonld your-export.jsonld
```
