# DQ02-missing-primary-contact: Organization profile with no primary contact

The OrganizationProfile has no `hasPrimaryContact` and there is no Person node.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Sample file `SPO4missingcontactperson20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-MISSING-CONTACT` | `https://tamarack-youth.example/OrganizationProfile/Tamarack/2025/` | `sff:hasPrimaryContact` | hasPrimaryContact is optional in SHACL, but SFF reports should name a contact person. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ02-missing-primary-contact/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ02-missing-primary-contact/capsule.jsonld
```
