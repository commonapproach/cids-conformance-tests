# V01-indicator-multiple-outcomes: One Indicator linked to several Outcomes

Northwind Food Recovery Society (Basic tier). The Indicator "Tonnes of food recovered" serves three Outcomes, and the Outcome "Improved food security" is measured by two Indicators.

**Category:** Valid  
**Based on:** New. No sample capsule linked an Indicator to more than one Outcome, and duplicating such an Indicator on export is a known round-trip failure.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- `cids:forOutcome` with three values on one Indicator, and the matching `cids:hasIndicator` on each Outcome.
- An Outcome with two Indicators (many-to-many).
- A control Indicator with a single Outcome.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- `https://northwind-food.example/Indicator/TonnesFoodRecovered/` comes back as **one** Indicator node, not one copy per Outcome.
- That Indicator keeps all three `forOutcome` links, and each of the three Outcomes keeps its `hasIndicator` link back to it.
- Its four IndicatorReports still point at the one Indicator.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld
python -m cidsconformance dq capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld
python -m cidsconformance compare capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld your-export.jsonld
```
