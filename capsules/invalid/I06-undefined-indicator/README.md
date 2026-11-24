# I06-undefined-indicator: Link to an Indicator that isn't in the capsule

The Organization's `hasIndicator` lists an Indicator that is not defined anywhere in the capsule.

**Category:** Broken (fails SHACL)  
**Based on:** Several SPO samples and MultipleOrgs*.json reference Indicators and Outcomes that are never defined. I13 covers an undefined Outcome.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/Organization/Tamarack/` | `cids:hasIndicator` | `sh:ClassConstraintComponent` | https://tamarack-youth.example/Indicator/MentorHoursLogged/ is not defined as a cids:Indicator in the capsule. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I06-undefined-indicator/capsule.jsonld
```
