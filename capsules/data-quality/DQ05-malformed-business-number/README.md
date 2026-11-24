# DQ05-malformed-business-number: Business number in the wrong format

The CRA business number is `"123456789 RC0001 200"`: it has spaces and extra digits.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Sample file `SPO15identifierhaserrors20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-IDENTIFIER-FORMAT` | `https://tamarack-youth.example/OrganizationID/Tamarack/` | `org:hasIdentifier` | A CRA business number (BN15) is 9 digits, 2 letters and 4 digits, with no spaces, e.g. 123456789RC0001. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ05-malformed-business-number/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ05-malformed-business-number/capsule.jsonld
```
