# I01-address-missing-postal-code: Address with no postal code

The Address has a street, city, province and country, but no `postalCode`.

**Category:** Broken (fails SHACL)  
**Based on:** Sample file `SPO2incompleteaddressnopostalcode20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/Address/Tamarack/` | `cids:postalCode` | `sh:MinCountConstraintComponent` | Every Address needs exactly one postalCode. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I01-address-missing-postal-code/capsule.jsonld
```
