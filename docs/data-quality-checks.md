# Data-quality checks

SHACL checks structure: a required property is missing, a value has the wrong type, a link points at the wrong kind of node. Some problems in the 2025 sample set are valid CIDS but almost certainly wrong, and SHACL can't see them. These checks find them.

A data-quality (DQ) finding is a **warning**. It doesn't make a capsule invalid. The capsules in `capsules/data-quality/` all pass SHACL and each one triggers one DQ check.

Run the checks on any capsule:

```sh
python -m cidsconformance dq path/to/capsule.jsonld
python -m cidsconformance dq path/to/capsule.jsonld --json
python -m cidsconformance dq path/to/capsule.jsonld --fail-on-findings   # exit 1 if anything is found
```

The checks are in [`cidsconformance/dq.py`](../cidsconformance/dq.py).

| Code | Reported on | What triggers it | Capsule |
|---|---|---|---|
| `DQ-MISSING-ADDRESS` | Organization | A reporting organization (one with Indicators, Outcomes or an SFF OrganizationProfile) has no `cids:hasAddress`. | DQ01 |
| `DQ-MISSING-CONTACT` | sff:OrganizationProfile | No `sff:hasPrimaryContact`. | DQ02 |
| `DQ-INDICATOR-NO-REPORTS` | Indicator | No IndicatorReport is linked to it, either through `hasIndicatorReport` or through a report's `forIndicator`. | DQ03 |
| `DQ-MISSING-ORG-ID` | Organization | An organization with an SFF OrganizationProfile has no `org:hasID`. Not checked for Basic tier capsules, which often have no IDs. | DQ04 |
| `DQ-IDENTIFIER-FORMAT` | org:OrganizationID | `hasIdentifier` contains whitespace, or is issued by the Canada Revenue Agency (`CanadianCorporateRegistries#cra`) and isn't a 15-character business number (`^\d{9}[A-Z]{2}\d{4}$`, e.g. `123456789RC0001`). | DQ05 |
| `DQ-OUTLIER` | the report's i72:Measure | An Indicator has at least 4 numeric reports, and one value is more than 5× (or less than 1/5 of) the median of the others. | DQ06 |
| `DQ-TIME-SERIES-GAP` | Indicator | Sorted by start date, the gap between one report's end and the next one's start is more than half the Indicator's usual report length. This works for annual, quarterly and fiscal-year series. | DQ07 |
| `DQ-NON-NUMERIC-VALUE` | the report's i72:Measure | `hasNumericalValue` is empty or isn't a plain number (e.g. `""`, `"N/A"`, `"1,200"`). SHACL can't catch this because the property is typed `xsd:string`. | DQ08 |
| `DQ-ADDRESS-FIELDS-SWAPPED` | Address | `postalCode` is a country name, or `addressCountry` looks like a postal or ZIP code. | DQ09 |
| `DQ-POSTAL-CODE-FORMAT` | Address | The country is Canada and the postal code isn't in `A1A 1A1` form. | none |
| `DQ-UNKNOWN-UNIT` | Indicator or i72:Measure | `i72:unit_of_measure` is a text value, or an IRI that is neither in the CIDS units list (`UnitsOfMeasureList.ttl`) nor defined in the capsule with an `i72:` unit type. | DQ10 |

Every valid capsule in `capsules/valid/` produces no DQ findings. The suite checks this.

## Thresholds

The outlier factor (5×), the minimum series length (4), and the gap tolerance (half a period) are set at the top of `dq.py`. They are starting points. The sample set's outlier (a B Impact score of 790 among scores of 80 to 95) is far past them, and real data will show whether they should be tighter.
