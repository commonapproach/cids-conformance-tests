# I08-indicator-missing-unit-description: Indicator with no unit description

The B Impact Indicator has no `unitDescription`.

**Category:** Broken (fails SHACL)  
**Based on:** New. A required Basic tier field that spreadsheet exports often leave blank. I14 covers a missing `forOrganization`.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/Indicator/BImpactScore/` | `cids:unitDescription` | `sh:MinCountConstraintComponent` | Every Indicator needs a unitDescription. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I08-indicator-missing-unit-description/capsule.jsonld
```
