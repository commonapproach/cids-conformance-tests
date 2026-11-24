# I13-undefined-outcome: Link to an Outcome that isn't in the capsule

An Indicator's `forOutcome` lists an Outcome that is not defined anywhere in the capsule.

**Category:** Broken (fails SHACL)  
**Based on:** Several SPO samples and MultipleOrgs*.json reference Indicators and Outcomes that are never defined. I06 covers an undefined Indicator.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/Indicator/YouthPlacedInJobs/` | `cids:forOutcome` | `sh:ClassConstraintComponent` | https://tamarack-youth.example/Outcome/HigherYouthIncomes/ is not defined as a cids:Outcome in the capsule. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I13-undefined-outcome/capsule.jsonld
```
