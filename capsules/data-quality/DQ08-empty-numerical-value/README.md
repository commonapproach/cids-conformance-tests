# DQ08-empty-numerical-value: Empty value in an IndicatorReport

The 2022 B Impact report has `hasNumericalValue: ""` (an empty string).

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** SPO6missingvalueinanindicatorreportGallo20261103.json, SPO8... and SPO21... (2022 B Corp value). An empty string passes SHACL because hasNumericalValue is typed xsd:string.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-NON-NUMERIC-VALUE` | `https://tamarack-youth.example/IndicatorReport/BImpactScore/2022 / i72:value` | `i72:hasNumericalValue` | The value is empty. Either remove the report or fill in the number. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ08-empty-numerical-value/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ08-empty-numerical-value/capsule.jsonld
```
