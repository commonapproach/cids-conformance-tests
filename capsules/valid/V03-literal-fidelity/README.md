# V03-literal-fidelity: Text, numbers and dates that must survive unchanged

Coopérative d’habitation du Ruisseau-Vert (Basic tier). Values that importers often change by accident.

**Category:** Valid  
**Based on:** New. The Airtable samples had trailing spaces in names, which is a common place for data to change.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- French accents, a curly apostrophe (’), guillemets, an em dash, and Inuktitut syllabics.
- A description with line breaks, a tab, double quotes, `&` and `<...>`.
- A name with a trailing space (`"Households housed "`).
- A description longer than 1,000 characters.
- Number strings with trailing zeros (`"27.50"`, `"1250000.00"`) and negatives (`"-0.75"`).
- Dates written with `Z`, `+00:00`, and fractional seconds (`.999`).

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- Text is not trimmed, re-encoded, HTML-escaped or truncated.
- `hasNumericalValue` strings are not converted to numbers and back: `"27.50"` must not become `"27.5"` and `"1250000.00"` must not become `"1250000"` or `"1.25E6"`.
- Dates keep their written form. Converting `2023-01-01T05:00:00Z` to `2023-01-01T00:00:00-05:00` is the same instant. `compare` reports it as `LITERAL_REFORMATTED`, which only fails with `--strict`.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V03-literal-fidelity/capsule.jsonld
python -m cidsconformance dq capsules/valid/V03-literal-fidelity/capsule.jsonld
python -m cidsconformance compare capsules/valid/V03-literal-fidelity/capsule.jsonld your-export.jsonld
```
