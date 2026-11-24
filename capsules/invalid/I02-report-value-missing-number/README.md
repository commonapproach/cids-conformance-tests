# I02-report-value-missing-number: IndicatorReport value with no number

The 2022 "Youth placed in jobs" report has a `value` Measure with a unit but no `hasNumericalValue`.

**Category:** Broken (fails SHACL)  
**Based on:** Sample file `SPO8indicatorreportwithmissingvalues20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/IndicatorReport/YouthPlacedInJobs/2022 / i72:value` | `i72:hasNumericalValue` | `sh:MinCountConstraintComponent` | The Measure behind a report's value needs exactly one hasNumericalValue. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I02-report-value-missing-number/capsule.jsonld
```
