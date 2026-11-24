# DQ04-missing-organization-id: Organization with no identifier

The Organization has no `hasID` and there is no OrganizationID node.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Sample file `SPO9missingidentifier20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-MISSING-ORG-ID` | `https://tamarack-youth.example/Organization/Tamarack/` | `org:hasID` | Without a business number or registry ID, the organization can't be matched across reports. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ04-missing-organization-id/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ04-missing-organization-id/capsule.jsonld
```
