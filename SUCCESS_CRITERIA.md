# Success criteria (DRAFT, for review)

> **Status: draft.** To be agreed with Common Approach before this suite is published or sent to vendors. The decisions at the end were made while drafting and need Common Approach's sign-off.

These criteria are for software that **imports and exports** CIDS capsules, such as impact-reporting platforms. "The suite" means this repository at a tagged version, with the reference data in `reference/`.

## Required

A product conforms to the suite when all of these hold.

### 1. It imports every valid capsule

Every capsule in [`capsules/valid/`](capsules/valid/) imports without errors. For V06, import `part-1-up-to-2024.jsonld` and then `part-2-2025.jsonld` into the same workspace.

### 2. It exports exactly what it imported

For each valid capsule, import it, export it straight away, and compare:

```sh
python -m cidsconformance compare capsules/valid/<capsule>/capsule.jsonld your-export.jsonld
```

The result must be **PASS**. That means:

| Must not happen | `compare` reports it as |
|---|---|
| A node is lost | `MISSING_NODE` |
| A property value is lost | `MISSING_TRIPLE` |
| A node comes back with a different IRI | `IRI_CHANGED` |
| One node comes back as several (e.g. one Indicator per Outcome) | `DUPLICATE_NODE` |
| A value or link changes | `VALUE_CHANGED` |
| A value moves to a different property (e.g. `cids:hasComment` → `sff:hasComment`) | `PREDICATE_CHANGED` |
| Something is added that wasn't imported | `EXTRA_NODE`, `EXTRA_TRIPLE` (see decision 1) |

What is allowed: any JSON-LD layout (`@graph` or array, any key order, compact or full IRIs, nested or flat), Turtle instead of JSON-LD, and blank nodes with different labels. `compare` works on the RDF graph, so none of these count as differences.

For V06, after both imports the export must match `expected-after-both-parts.jsonld`.

This includes the Theme and Characteristic nodes the capsules declare for codelist codes (SDGs, populations served, equity-deserving groups): they are part of the capsule and must be exported too (decision 3).

Each capsule's `README.md` lists what that capsule is most likely to break.

### 3. Its exports are valid

Every exported capsule passes SHACL validation:

```sh
python -m cidsconformance validate your-export.jsonld        # Basic tier and SFF
```

The command exits with 0 and reports no violations. Basic tier and SFF are what's required, for every capsule including V10 and V11 (decision 4).

### 4. It doesn't accept broken data silently

Each capsule in [`capsules/invalid/`](capsules/invalid/) has exactly one known problem. For each one, the product either rejects it or imports it while showing the user the problem described in the capsule's `README.md`. It must not import it silently, and it must not "fix" the data without telling the user.

### 5. It keeps data-quality problems as they are

Capsules in [`capsules/data-quality/`](capsules/data-quality/) are valid CIDS with suspicious content. The product imports them and exports them unchanged (criterion 2 applies). It must not drop the empty value, swap the address fields back, or similar.

## Recommended

- **Strict round trip:** `compare --strict` also passes. This means literals keep their exact written form, e.g. `2023-01-01T05:00:00Z` isn't rewritten as `2023-01-01T00:00:00-05:00`.
- **Tier shapes:** the V10 export also passes `--profile essential`, and the V11 export `--profile essential --profile full`. These use corrected copies of the published tier shapes, which can't be passed as published (see [reference/SOURCES.md](reference/SOURCES.md#corrections-to-the-published-shapes)).
- **Data-quality warnings:** when importing a data-quality capsule, the product warns about the finding listed in its `README.md`.

## How a vendor reports results

Fill in [docs/vendor-results-template.md](docs/vendor-results-template.md) (or the CSV version for spreadsheets). It lists every capsule, and asks for the product version and the suite version (git tag or commit). Attach the `compare --json` output for every FAIL.

## Decisions

These were made while drafting. Common Approach should confirm them before the criteria are published.

1. **Extra data fails.** An export that adds data that wasn't imported (import timestamps, default values) fails `compare`. A vendor that adds its own metadata leaves those properties out of the comparison with `--ignore-predicate IRI` and lists them in its results.
2. **Reformatted dates pass.** The same moment written differently (another UTC offset, `Z` instead of `+00:00`) passes. Keeping the exact text is recommended (`compare --strict`).
3. **Codelist nodes must be exported.** The Theme and Characteristic nodes the capsules declare for codelist codes are part of the capsule, so a round trip must keep them, not just the links to the codelist IRIs.
4. **Basic tier and SFF are required; the tier shapes are recommended.** The published Essential and Full tier shapes can't be passed as published, so they are recommended (against corrected copies), not required, until they are fixed.
5. **B Lab stays in V09.** It's the standards body that B Corp data refers to, not a reporting organization; every reporting organization in the capsules is fictional. The B Impact Assessment Code IRI in V09 stays a placeholder.
6. **Data-quality thresholds stay as starting points:** an outlier is more than 5× (or less than 1/5 of) the median of at least 4 reports; a gap is longer than half the usual reporting period. See [docs/data-quality-checks.md](docs/data-quality-checks.md).
7. **The original sample files stay out of this public repository.** The capsules rebuild each scenario with fictional data; [source/README.md](source/README.md) maps each capsule to its original.

## Problems in the published CIDS files

Problems found in the published CIDS shapes, contexts and codelists while building the suite are reported in the CIDS repository, not tracked here. [reference/SOURCES.md](reference/SOURCES.md) explains the corrections the tools apply when loading the tier shapes, and why.
