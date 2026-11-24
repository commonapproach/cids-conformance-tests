# V04-uncommon-properties: Less common CIDS properties

Maple Hollow Learning Collective (Basic tier plus optional properties). Uses properties that are valid CIDS but rarely appear in Basic tier exports, so importers often drop them.

**Category:** Valid  
**Based on:** New. There was no agreed list of uncommon properties, so these were picked from the CIDS ontology and the SFF/Full tier shapes.

## Files

- `capsule.jsonld`: the capsule in JSON-LD. `capsule.ttl` has the same data in Turtle.
- `expected.json`: the expected validation results, in machine-readable form.

## What it tests

- Organization: `hasWebAddress`, `hasPurpose`, `hasDescription`, `numberOfEmployees`, `hasContact` → Person, `hasCharacteristic`, `hasID` → OrganizationID.
- Address: `extendedAddress`, `postOfficeBoxNumber`.
- Indicator: `hasIdentifier`, `hasCode` → Code, `definedBy`, `cids:describesPopulation` → i72:Population (no context term, so a prefixed key), `hasBaseline` and `hasThreshold` (each an i72:Measure), and two `forTheme` values.
- Outcome: `hasCode`, `canProduce` → another Outcome.
- Theme: `relatesTo` → another Theme, `hasCode`.
- Code: `definedBy`, `hasIdentifier`, `hasSpecification` (xsd:anyURI), `schema:codeValue`.
- A node with two types (`cids:StandardsOrganization` and `cids:Organization`).
- IndicatorReport with two `cids:hasComment` values.

## What must come back unchanged after import and export

- Every node comes back with exactly the same `@id`. IRIs are case-sensitive and are not re-minted, shortened or normalized.
- Every property value comes back with exactly the same text. Numbers in `hasNumericalValue` are strings and keep their exact form.
- No node is duplicated and no extra nodes are added.
- All of the properties listed above come back, with their values.
- `hasBaseline` and `hasThreshold` come back as Measures with both `hasNumericalValue` and `unit_of_measure`.
- The comments come back as `cids:hasComment`. **Watch out:** the SFF context maps the short key `hasComment` to `sff:hasComment`, so an exporter that writes `"hasComment"` with both contexts loaded produces the wrong property. `compare` reports this as `PREDICATE_CHANGED`.
- The Council node keeps both of its types.

## Expected validation result

Passes Basic tier and SFF SHACL validation with no results at all (no violations, warnings or info), and the data-quality checks find nothing.

## Check it yourself

```sh
python -m cidsconformance validate capsules/valid/V04-uncommon-properties/capsule.jsonld
python -m cidsconformance dq capsules/valid/V04-uncommon-properties/capsule.jsonld
python -m cidsconformance compare capsules/valid/V04-uncommon-properties/capsule.jsonld your-export.jsonld
```
