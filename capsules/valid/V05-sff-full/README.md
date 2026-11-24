# V05-sff-full: Full, realistic SFF capsule for one organization

Riverbend Community Energy Co-operative: every SFF node type, three Indicators with seven years of annual reports (2019-2025), shaped like the Airtable sample exports.

**Category:** Valid  
**Based on:** Rebuilt from the shape of SampleOrg1.json (2025 sample set) with fictional data and the defects fixed.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- Organization, Address, OrganizationID (CRA business number), Person, OrganizationProfile, two TeamProfiles with EDGProfiles, FundingStatus, ReportInfo.
- SFF codelist references: sector, locality, province, population served, organization type, funding state, equity-deserving groups.
- Theme nodes for SDG 7 and 13, with the same names as the SDG codelist.
- Unit definitions (`i72:Singular_unit` etc.) and an `i72:Population`, as in the Airtable exports.
- An Indicator linked to two Outcomes.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- All 21 IndicatorReports come back with their exact values and periods.
- Codelist IRIs (`https://codelist.commonapproach.org/...`, `https://metadata.un.org/sdg/...`) come back exactly. They are not swapped for labels.
- `hasTeamSize`, `hasEDGSize` and `hasSize` stay `xsd:nonNegativeInteger`, and `reportedDate` stays `xsd:dateTime`.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V05-sff-full/capsule.jsonld
python -m cidsconformance dq capsules/valid/V05-sff-full/capsule.jsonld
python -m cidsconformance compare capsules/valid/V05-sff-full/capsule.jsonld your-export.jsonld
```
