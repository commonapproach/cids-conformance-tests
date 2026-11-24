# I11-organization-missing-legal-name: Organization with no legal name

The Organization node has no `hasLegalName`.

**Category:** Broken (fails SHACL)  
**Based on:** New.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/Organization/Tamarack/` | `org:hasLegalName` | `sh:MinCountConstraintComponent` | Every Organization needs exactly one legal name. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I11-organization-missing-legal-name/capsule.jsonld
```
