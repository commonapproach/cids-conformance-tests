# I10-negative-team-size: Negative team size

The management TeamProfile has `hasTeamSize: -3`.

**Category:** Broken (fails SHACL)  
**Based on:** New. Checks that importers enforce xsd:nonNegativeInteger.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| SFF | Violation | `https://tamarack-youth.example/TeamProfile/Tamarack/Management/2025/` | `sff:hasTeamSize` | `sh:DatatypeConstraintComponent` | hasTeamSize must be a whole number of 0 or more. |

Basic tier validation passes: these properties are only checked by the SFF shapes.

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I10-negative-team-size/capsule.jsonld
```
