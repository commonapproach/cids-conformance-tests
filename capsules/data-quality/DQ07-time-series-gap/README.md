# DQ07-time-series-gap: Missing year in a time series

"Youth placed in jobs" has annual reports for 2019-2024 except 2022.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Sample file `SPO21missingdatainatimeseries2022missing20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-TIME-SERIES-GAP` | `https://tamarack-youth.example/Indicator/YouthPlacedInJobs/` | `cids:hasIndicatorReport` | No report covers 2022, although there are reports before and after it. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ07-time-series-gap/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ07-time-series-gap/capsule.jsonld
```
