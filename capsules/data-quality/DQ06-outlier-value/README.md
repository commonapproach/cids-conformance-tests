# DQ06-outlier-value: B Impact score far too high

The 2024 B Impact score is 790. The other years are between 82 and 94, and the scale only goes to 200.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Sample file `SPO5anomolousdataBScoretoohigh20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-OUTLIER` | `https://tamarack-youth.example/IndicatorReport/BImpactScore/2024 / i72:value` | `i72:hasNumericalValue` | 790 is more than 5 times the median of the other B Impact reports. Likely a typo (79.0?). |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ06-outlier-value/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ06-outlier-value/capsule.jsonld
```
