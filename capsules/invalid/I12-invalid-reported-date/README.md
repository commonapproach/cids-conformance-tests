# I12-invalid-reported-date: "Invalid date" as an OrganizationProfile's reportedDate

The OrganizationProfile's `reportedDate` is the text "Invalid date" instead of a date and time.

**Category:** Broken (fails SHACL)  
**Based on:** SPO*.json: every SPO sample has `reportedDate: "Invalid date"` (a spreadsheet export artifact).

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| SFF | Violation | `https://tamarack-youth.example/OrganizationProfile/Tamarack/2025/` | `sff:reportedDate` | `sh:DatatypeConstraintComponent` | reportedDate must be an xsd:dateTime such as 2025-03-31T00:00:00-04:00. |

Basic tier validation passes: these properties are only checked by the SFF shapes.

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I12-invalid-reported-date/capsule.jsonld
```
