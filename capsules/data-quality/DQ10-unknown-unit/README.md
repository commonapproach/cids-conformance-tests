# DQ10-unknown-unit: Unit of measure that isn't defined anywhere

The 2024 "Youth placed in jobs" value uses the unit `https://tamarack-youth.example/Unit/Youth`, which is not in the CIDS units list or the capsule.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** SPO21... uses `unit_of_measure: "Days"` (a label instead of a unit IRI, e.g. cids:dayUnit).

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-UNKNOWN-UNIT` | `https://tamarack-youth.example/IndicatorReport/YouthPlacedInJobs/2024 / i72:value` | `i72:unit_of_measure` | Use a unit from the CIDS units list (here cids:countUnit), or define the unit in the capsule. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ10-unknown-unit/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ10-unknown-unit/capsule.jsonld
```
