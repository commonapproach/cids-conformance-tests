# Where the scenarios came from

The capsules started from the 2025 sample set, made for the 2025 Propel Analyst training and exported from Airtable. The notes that came with the set:

- Preload the demo with "Multiple Orgs for all years up to 2024".
- Import "Multiple Orgs only recent years" to show how new years can be added.
- Sample Org 1, 10 and 11 show how individual organizations can be added.
- Missing from this sample data: portfolio organizations that report by quarter, mismatched year ends, and B Corp Assessments as Indicator + hasCode.

**The original files are not in this repository.** Some of them contain real-looking street addresses, product names and email addresses, and this repository is public. Each capsule was rebuilt from scratch with fictional data, keeping the scenario the original file was meant to show. The table below says which original each capsule is based on.

## Which capsule replaces which sample file

| Sample file | Scenario | Capsule |
|---|---|---|
| MultipleOrgsupto2024data.json + MultipleOrgsonlyrecentyear.json | Load years up to 2024, then add the latest year | V06-portfolio-incremental-import |
| SampleOrg1.json (and 10, 11) | A single organization, full SFF data | V05-sff-full |
| (gap in the notes) | Quarterly reporting | V07-quarterly-reporting |
| (gap in the notes) | Mismatched year ends | V08-mismatched-year-ends |
| (gap in the notes) | B Corp as Indicator + hasCode | V09-bcorp-indicator-hascode |
| (asked for in the updated ticket) | A full Essential tier capsule | V10-essential-tier |
| (asked for in the updated ticket) | A full Full tier capsule | V11-full-tier |
| SPO1missingaddress | Missing address | DQ01-missing-address |
| SPO2incompleteaddressnopostalcode | No postal code | I01-address-missing-postal-code |
| SPO3indicatorwithoutanyindicatorreports | Indicator with no reports | DQ03-indicator-without-reports |
| SPO4missingcontactperson | No contact person | DQ02-missing-primary-contact |
| SPO5anomolousdataBScoretoohigh | B score of 790 | DQ06-outlier-value |
| SPO6missingvalueinanindicatorreport | Empty value | DQ08-empty-numerical-value |
| SPO8indicatorreportwithmissingvalues | Report value with no number | I02-report-value-missing-number (value missing) and DQ08 (value `""`) |
| SPO9missingidentifier | No OrganizationID | DQ04-missing-organization-id |
| SPO10identifiermissingvalues | OrganizationID with no identifier or issuer | I03-organization-id-missing-values |
| SPO15identifierhaserrors | Business number `"… RC0001 200"` | DQ05-malformed-business-number |
| SPO21missingdatainatimeseries | Missing 2022 | DQ07-time-series-gap |

Each broken capsule has exactly one problem, as the ticket asks. Where a sample file had several problems, each one has its own capsule.

Several SPO scenarios (missing address, missing contact, no reports, no ID, outlier, gap) aren't SHACL violations under the current shapes: those properties are optional, or the value is a valid string. They are in the separate **data-quality** category. See [docs/data-quality-checks.md](../docs/data-quality-checks.md).

## Problems found in the sample files

These affect the sample files themselves, not the capsules. Several of them became broken or data-quality capsules.

- **Postal code and country swapped** in every Address of SampleOrg* and MultipleOrgs* (`postalCode: "Canada"`). → DQ09
- **B Corp IndicatorReports have no `forIndicator`**, and their unit is `unspecifiedUnit`. → I05
- **Empty placeholder nodes:** `org:OrganizationID` with no `hasIdentifier`/`issuedBy` (→ I03), and `sff:ReportInfo` with only `forOrganization` (→ I07).
- **Links to nodes that are never defined**: several SPO files (e.g. SPO2, SPO4, SPO6) link to Outcomes and Indicators that are never declared. → I06 (an Indicator) and I13 (an Outcome)
- **`"Invalid date"` in date fields** in every SPO file. → I04 (`endedAtTime`) and I12 (`reportedDate`)
- **A unit given as text:** `unit_of_measure: "Days"` instead of `cids:dayUnit`. → DQ10
- **IRIs with a space** (an IRI ending in `/ copy`) and **double slashes** (`https://<sample domain>//Outcome/<name>`). → V02 tests that legal-but-unusual IRIs survive (including `//` and an encoded `%20`)
- **One report listed under two Indicators** (SPO16). → I09
- **Mixed `http`/`https` for the same SDG** (`http://metadata.un.org/sdg/13` and `https://…`). Only the `https` form is in the SDG codelist.
- **Codelist IRIs with an extra `codeLists/` path segment** (`https://codelist.commonapproach.org/codeLists/EquityDeservingGroupsESDC#edg1`). The codelist files define `https://codelist.commonapproach.org/EquityDeservingGroupsESDC#edg1`, so these don't resolve.
- **The same Theme `@id` twice**, once without `hasName`.
- **Names and dates that don't match:** reports whose name gives one year but whose dates are in the next, Indicators named in gigatonnes using `cids:megatonne`, and a truncated IRI ending in a three-digit year.
- **Names with trailing spaces** (an Indicator name ending in a space). → V03 checks these survive unchanged
- **No Indicator is linked to more than one Outcome.** → V01 was added for this
