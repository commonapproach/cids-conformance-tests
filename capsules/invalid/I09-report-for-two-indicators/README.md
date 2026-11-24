# I09-report-for-two-indicators: One IndicatorReport claimed by two Indicators

The 2024 B Impact report has two `forIndicator` values, and both Indicators list it in `hasIndicatorReport`.

**Category:** Broken (fails SHACL)  
**Based on:** SPO16 in MultipleOrgs*.json: one report is listed under two Indicators. A merge of duplicate Indicators produces the same thing.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/IndicatorReport/BImpactScore/2024` | `cids:forIndicator` | `sh:MaxCountConstraintComponent` | An IndicatorReport reports on exactly one Indicator. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I09-report-for-two-indicators/capsule.jsonld
```
