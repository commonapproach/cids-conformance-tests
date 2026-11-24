# I07-empty-report-info: ReportInfo with only an organization

The ReportInfo node has `forOrganization` but no name and no reporting period.

**Category:** Broken (fails SHACL)  
**Based on:** Every ReportInfo in the Airtable sample exports looks like this.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## Expected validation result

SHACL validation must report exactly these results (and nothing else):

| Shapes | Severity | Focus node | Property | Constraint | Why |
|---|---|---|---|---|---|
| SFF | Violation | `https://tamarack-youth.example/ReportInfo/Tamarack/2024/` | `org:hasName` | `sh:MinCountConstraintComponent` | ReportInfo needs a name. |
| SFF | Violation | `https://tamarack-youth.example/ReportInfo/Tamarack/2024/` | `prov:startedAtTime` | `sh:MinCountConstraintComponent` | ReportInfo needs the start of the reporting period. |
| SFF | Violation | `https://tamarack-youth.example/ReportInfo/Tamarack/2024/` | `prov:endedAtTime` | `sh:MinCountConstraintComponent` | ReportInfo needs the end of the reporting period. |

This is one problem: SHACL reports it as 3 results, one per missing or bad property.

Basic tier validation passes: these properties are only checked by the SFF shapes.

## What an importer should do

An importer should reject this capsule, or import it while clearly reporting the problem described above. It must not quietly fix or drop the bad data.

## Check it yourself

```sh
python -m cidsconformance validate capsules/invalid/I07-empty-report-info/capsule.jsonld
```
