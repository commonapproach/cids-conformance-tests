# V02-stable-uris: IRIs that must survive unchanged

Kestrel Community Arts Society (Basic tier). Every node uses a different style of IRI.

**Category:** Valid  
**Based on:** New. Based on the IRI problems in the Airtable sample exports (double slashes, spaces, mixed http/https).

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- `http:` (not `https:`) IRI for the Organization.
- A port number (`:8443`), a `#fragment`, and a double slash (`//Outcome`).
- Two Indicators whose IRIs differ only by letter case and a trailing slash. They are different nodes.
- `urn:uuid:` and `tag:` IRIs.
- A query string with `&`, percent-encoded characters (`%C3%A9`) and an encoded space (`%20`).

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- Each IRI comes back byte-for-byte: no added or removed trailing slash, no lower-casing, no `http`→`https`, no decoding of `%C3%A9` or `%20`, no collapsing of `//`.
- `.../Indicator/Workshops` and `.../Indicator/workshops/` stay two separate Indicators.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V02-stable-uris/capsule.jsonld
python -m cidsconformance dq capsules/valid/V02-stable-uris/capsule.jsonld
python -m cidsconformance compare capsules/valid/V02-stable-uris/capsule.jsonld your-export.jsonld
```
