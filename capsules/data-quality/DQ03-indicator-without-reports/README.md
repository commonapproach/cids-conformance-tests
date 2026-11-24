# DQ03-indicator-without-reports: Indicator with no reports

A third Indicator, "Mentor hours logged", is defined and linked, but has no IndicatorReports.

**Category:** Data quality (passes SHACL, flagged by DQ checks)  
**Based on:** Sample file `SPO3indicatorwithoutanyindicatorreports20261103.json` from the 2025 sample set

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results.

The data-quality checks must report exactly:

| Code | Node | Property | Why |
|---|---|---|---|
| `DQ-INDICATOR-NO-REPORTS` | `https://tamarack-youth.example/Indicator/MentorHoursLogged/` | `cids:hasIndicatorReport` | An Indicator with no reports carries no data. Usually the reports were lost or never entered. |

## What an importer should do

The capsule passes SHACL validation, so an importer can accept it. A good importer (or a validator run before import) should warn the user about the finding listed above. It should still import and export the data unchanged.

## Check it yourself

```sh
python -m cidsconformance validate capsules/data-quality/DQ03-indicator-without-reports/capsule.jsonld
python -m cidsconformance dq capsules/data-quality/DQ03-indicator-without-reports/capsule.jsonld
```
