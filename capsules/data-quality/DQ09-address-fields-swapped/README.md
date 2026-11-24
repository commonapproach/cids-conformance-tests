# DQ09-address-fields-swapped: Postal code and country swapped

The Address has `postalCode: "Canada"` and `addressCountry: "P3E 0A1"`.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Every Address in the Airtable sample exports (SampleOrg*, MultipleOrgs*) has these two fields swapped.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-ADDRESS-FIELDS-SWAPPED` | `https://tamarack-youth.example/Address/Tamarack/` | `cids:postalCode` | Both fields are plain strings, so SHACL can't tell they are in the wrong places. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ09-address-fields-swapped/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ09-address-fields-swapped/capsule.jsonld
```
