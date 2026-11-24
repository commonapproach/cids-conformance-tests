# I14-indicator-missing-organization: Indicator with no organization

The B Impact Indicator has no `forOrganization`. The Organization still lists it in `hasIndicator`.

**Category:** Broken (fails SHACL)  
**Based on:** New. A required Basic tier field that spreadsheet exports often leave blank. I08 covers a missing `unitDescription`.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/Indicator/BImpactScore/` | `cids:forOrganization` | `sh:MinCountConstraintComponent` | Every Indicator must say which Organization it belongs to. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I14-indicator-missing-organization/capsule.jsonld
```
