# I04-invalid-date: "Invalid date" as a report's end date

The 2024 "Youth placed in jobs" report's `endedAtTime` is the text "Invalid date" instead of a date and time.

**Category:** Broken (fails SHACL)  
**Based on:** All of the SPO*.json samples have "Invalid date" in date fields (a spreadsheet export artifact). I12 covers the same text in `reportedDate`.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| Basic + SFF | Violation | `https://tamarack-youth.example/IndicatorReport/YouthPlacedInJobs/2024` | `prov:endedAtTime` | `sh:DatatypeConstraintComponent` | endedAtTime must be an xsd:dateTime. |

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I04-invalid-date/capsule.jsonld
```
