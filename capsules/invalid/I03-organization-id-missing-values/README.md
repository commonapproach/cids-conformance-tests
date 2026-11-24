# I03-organization-id-missing-values: OrganizationID with no identifier and no issuer

The OrganizationID node exists but has neither `hasIdentifier` nor `issuedBy`.

**Category:** Broken (fails SHACL)  
**Based on:** Sample file `SPO10identifiermissingvalues20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| SFF | Violation | `https://tamarack-youth.example/OrganizationID/Tamarack/` | `org:hasIdentifier` | `sh:MinCountConstraintComponent` | An OrganizationID needs the identifier itself (e.g. the business number). |
| SFF | Violation | `https://tamarack-youth.example/OrganizationID/Tamarack/` | `org:issuedBy` | `sh:MinCountConstraintComponent` | An OrganizationID needs the organization that issued it (e.g. Canada Revenue Agency). |

This is one problem: SHACL reports it as 2 results, one per missing or bad property.

Basic tier validation passes: these properties are only checked by the SFF shapes.

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I03-organization-id-missing-values/capsule.jsonld
```
