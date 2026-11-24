# CIDS Conformance Tests

A conformance test suite for software that imports and exports data in the [Common Impact Data Standard (CIDS)](https://ontology.commonapproach.org/cids), including the Social Finance Fund (SFF) extension.

The suite has three parts:

- **Test capsules**: CIDS files with known content and a known expected result.
- **A round-trip check** (`compare`): tells you exactly what your software changed when it imported a capsule and exported it again.
- **A validator** (`validate`, `dq`): SHACL validation against the Basic tier and SFF shapes (and the Essential and Full tier shapes on request), plus data-quality checks.

All data in the capsules is fictional. Organization web and email domains use the reserved `.example` domain, and business numbers fail the CRA check digit.

> **Status:** draft. The [success criteria](SUCCESS_CRITERIA.md) are still being agreed.

## The capsules

There are 35 capsules in [`capsules/`](capsules/README.md). Each one has a `README.md` saying what it tests and what must survive, plus an `expected.json` with the expected results in machine-readable form.

| Category | What it means | Capsules |
|---|---|---|
| **Valid** | Passes Basic tier and SFF SHACL validation with no results at all (V10 and V11 also pass their tier's shapes). Import it, export it, and nothing may change. | 11 |
| **Broken** | Has exactly one known problem, and fails SHACL validation with exactly the listed results. Your software should reject it or report the problem. | 14 |
| **Data quality** | Passes SHACL, but contains something that is almost certainly wrong (an outlier, a missing year, swapped address fields). Flagged by the [data-quality checks](docs/data-quality-checks.md). | 10 |

The valid capsules:

| Capsule | What it tests |
|---|---|
| [V01-indicator-multiple-outcomes](capsules/valid/V01-indicator-multiple-outcomes/README.md) | One Indicator linked to three Outcomes must come back as one node |
| [V02-stable-uris](capsules/valid/V02-stable-uris/README.md) | Unusual but valid IRIs (case, trailing slash, `//`, `%20`, `urn:uuid:`, ports, fragments) come back byte-for-byte |
| [V03-literal-fidelity](capsules/valid/V03-literal-fidelity/README.md) | Accents, line breaks, trailing spaces, long text, `"27.50"`, time zones |
| [V04-uncommon-properties](capsules/valid/V04-uncommon-properties/README.md) | Rarely used CIDS properties (hasCode, hasBaseline, hasThreshold, relatesTo, hasID, ...) |
| [V05-sff-full](capsules/valid/V05-sff-full/README.md) | A full, realistic SFF capsule for one organization |
| [V06-portfolio-incremental-import](capsules/valid/V06-portfolio-incremental-import/README.md) | Three organizations, loaded up to 2024 and then 2025 added |
| [V07-quarterly-reporting](capsules/valid/V07-quarterly-reporting/README.md) | Quarterly reports, with daylight-saving offsets |
| [V08-mismatched-year-ends](capsules/valid/V08-mismatched-year-ends/README.md) | April–March and July–June fiscal years |
| [V09-bcorp-indicator-hascode](capsules/valid/V09-bcorp-indicator-hascode/README.md) | B Corp assessment as an Indicator with `hasCode` |
| [V10-essential-tier](capsules/valid/V10-essential-tier/README.md) | A full, realistic Essential tier capsule: targets, baselines, stakeholders, impact reports |
| [V11-full-tier](capsules/valid/V11-full-tier/README.md) | A full, realistic Full tier capsule: impact model, program, activities, inputs, outputs, risks, counterfactual |

Every capsule is provided as JSON-LD (`capsule.jsonld`, in the same layout as the Airtable/Excel CIDS exports) and Turtle (`capsule.ttl`). Both hold the same graph.

## Setup

You need Python 3.10 or newer.

```sh
git clone https://github.com/commonapproach/cids-conformance-tests.git
cd cids-conformance-tests
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

All commands below are run from the repository root.

## Testing your software

For each capsule in `capsules/valid/`:

1. **Import** `capsule.jsonld` (or `capsule.ttl`) into your software.
2. **Export** the same data as CIDS JSON-LD or Turtle, e.g. to `my-export.jsonld`.
3. **Compare** the export with what you imported:

   ```sh
   python -m cidsconformance compare capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld my-export.jsonld
   ```

4. **Validate** the export:

   ```sh
   python -m cidsconformance validate my-export.jsonld
   ```

   Basic tier and SFF are required. For V10 and V11, also checking `--profile essential` (and `--profile full` for V11) is recommended (see below).

For each capsule in `capsules/invalid/`, import it and check that your software rejects it or reports the problems listed in its `README.md`.

[SUCCESS_CRITERIA.md](SUCCESS_CRITERIA.md) has the full list of what counts as passing. Record your results in [docs/vendor-results-template.md](docs/vendor-results-template.md) (or the CSV version).

## Comparing an export with the import

`compare` parses both files into RDF graphs, so layout differences don't matter: JSON-LD vs Turtle, `@graph` vs array, key order, compact vs full IRIs, blank-node labels. It then explains what is different (IRIs shortened here):

```text
$ python -m cidsconformance compare capsules/valid/V01-indicator-multiple-outcomes/capsule.jsonld \
      examples/round-trip/V01-export-duplicated-indicator.jsonld
Imported: 153 triples   Exported: 177 triples
  DUPLICATE_NODE: 2

[FAIL] DUPLICATE_NODE  https://northwind-food.example/Indicator/TonnesFoodRecovered/  imported: …/TonnesFoodRecovered/  exported: …/TonnesFoodRecovered-2/
[FAIL] DUPLICATE_NODE  https://northwind-food.example/Indicator/TonnesFoodRecovered/  imported: …/TonnesFoodRecovered/  exported: …/TonnesFoodRecovered-3/

RESULT: FAIL
```

| Report | Meaning | Fails? |
|---|---|---|
| `MISSING_NODE` / `MISSING_TRIPLE` | Something in the import isn't in the export | yes |
| `IRI_CHANGED` | A node came back under a new IRI (matched by type and literal values) | yes |
| `DUPLICATE_NODE` | One imported node came back as two or more | yes |
| `VALUE_CHANGED` | Same property, different value (e.g. `"1115"` → `"1115.0"`) | yes |
| `PREDICATE_CHANGED` | Same value, different property (e.g. `cids:hasComment` → `sff:hasComment`) | yes |
| `EXTRA_NODE` / `EXTRA_TRIPLE` | The export added something | yes, unless `--allow-extra` |
| `LITERAL_REFORMATTED` | Same value, written differently (e.g. another time zone) | only with `--strict` |

Options:

- `--strict`: also fail on `LITERAL_REFORMATTED`.
- `--allow-extra`: list additions but don't fail on them.
- `--ignore-predicate IRI`: leave a property out entirely (repeatable). If your software adds its own metadata to exports (import timestamps, internal IDs, default values), leave those properties out this way and list them in your results. Otherwise they fail the comparison as `EXTRA_TRIPLE`s.
- `--json`: machine-readable output.

The exit code is 0 for PASS and 1 for FAIL, so `compare` can run in your own CI. [`examples/round-trip/`](examples/round-trip/README.md) has example exports showing each kind of failure.

## Validating a capsule

```sh
python -m cidsconformance validate my-file.jsonld                 # Basic tier and SFF
python -m cidsconformance validate my-file.jsonld --profile basic
python -m cidsconformance validate my-file.jsonld --profile essential --profile full
python -m cidsconformance validate my-file.jsonld --profile all   # all four
python -m cidsconformance validate my-file.jsonld --json
python -m cidsconformance dq my-file.jsonld                       # data-quality checks
```

Validation works the same way as the official `CIDS-validate.sh --codelists` script in the CIDS repo:

- The CIDS codelists are merged into the data before validating.
- No inference is run.
- Results on codelist nodes (`codelist.commonapproach.org`, `metadata.un.org`) are hidden. `--include-codelist-results` shows them.

The script uses pyshacl. [`scripts/jena_crosscheck.py`](scripts/jena_crosscheck.py) checks every expected result with Apache Jena, the engine the official script uses, and the two agree. CI runs it on every push.

Shapes, contexts and codelists are pinned in [`reference/`](reference/SOURCES.md), so nothing is downloaded and results are repeatable. `python -m cidsconformance refresh-reference` updates them.

**The published Essential and Full tier shapes have bugs** that make every capsule fail. For example, every "zero or more" property is written as "none allowed", so no Indicator may link to an Outcome. The pinned files are kept exactly as published, and the tools correct the bugs when loading them. [reference/SOURCES.md](reference/SOURCES.md#corrections-to-the-published-shapes) lists each correction. The Basic tier and SFF shapes need none.

**Properties without a context term.** Many Essential and Full tier properties (`forTarget`, `hasTarget`, `dateCreated`, `partOf`, `wasGeneratedBy`, `hasLikelihood`, ...) have no term in the published JSON-LD contexts. A JSON-LD processor silently drops a key it doesn't know, so V10 and V11 write these as prefixed keys (`"cids:forTarget"`, `"sch:dateCreated"`), which expand using the prefixes the contexts do define. Your exporter needs to do the same.

## Running the suite itself

```sh
python -m cidsconformance suite         # every capsule gives exactly its expected results
python -m pytest                        # the above, plus tests of compare and the generator
```

CI ([`.github/workflows/conformance.yml`](.github/workflows/conformance.yml)) runs both on every push (on Python 3.10 and 3.11), and runs the Jena cross-check. A separate, non-blocking job runs the capsules against the latest published shapes and codelists every week.

## Changing or adding capsules

The capsules are generated, so that each broken capsule is a single, known change to a clean base. Edit [`cidsconformance/generator/catalog.py`](cidsconformance/generator/catalog.py) and run:

```sh
python -m cidsconformance build
python -m cidsconformance suite
```

Don't edit the files in `capsules/` by hand. CI checks they match the generator. Expected results are written by hand in `catalog.py`, not copied from validator output.

## Repository layout

| Path | Contents |
|---|---|
| `capsules/` | The test capsules (generated) |
| `examples/round-trip/` | Example exports showing what `compare` reports (generated) |
| `cidsconformance/` | The command-line tools and the capsule generator |
| `reference/` | Pinned SHACL shapes, JSON-LD contexts and codelists |
| `docs/` | Data-quality check reference, and the vendor results template (generated) |
| `source/` | Where each scenario came from, and problems found in the original sample files |
| `scripts/` | Jena cross-check |
| `tests/` | pytest tests |
