# I05-report-without-indicator: IndicatorReport not linked to any Indicator

The 2019 B Impact report has no `forIndicator`, and no Indicator lists it.

**Category:** Broken (fails SHACL)  
**Based on:** The B Corp reports in the Airtable sample exports (SampleOrg*, MultipleOrgs*) have no forIndicator.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/IndicatorReport/BImpactScore/2019` | `cids:forIndicator` | `sh:MinCountConstraintComponent` | Every IndicatorReport must say which Indicator it reports on. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I05-report-without-indicator/capsule.jsonld
```
