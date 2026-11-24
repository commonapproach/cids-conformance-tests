# Reference data

The tools validate against pinned copies of the published CIDS files, so results don't change when the published files change. The weekly CI job also runs the suite against the latest published files and tells us if anything moved.

Retrieved on **2026-11-18**, except the Essential and Full tier shapes, retrieved on **2026-11-24**.

| File | Source |
|---|---|
| `shacl/cids.basictier.shacl.ttl` | https://ontology.commonapproach.org/validation/shacl/cids.basictier.shacl.ttl |
| `shacl/sff.shacl.ttl` | https://ontology.commonapproach.org/validation/shacl/sff.shacl.ttl |
| `shacl/cids.essentialtier.shacl.ttl` | https://ontology.commonapproach.org/validation/shacl/cids.essentialtier.shacl.ttl |
| `shacl/cids.fulltier.shacl.ttl` | https://ontology.commonapproach.org/validation/shacl/cids.fulltier.shacl.ttl |
| `contexts/cidsContext.jsonld` | https://ontology.commonapproach.org/contexts/cidsContext.jsonld |
| `contexts/sffContext.jsonld` | https://ontology.commonapproach.org/contexts/sffContext.jsonld |
| `codelists/<name>.ttl` (14 files) | `https://codelist.commonapproach.org/<name>.ttl`: the same list that `CIDS-validate.sh --codelists` uses |
| `codelists/cids-codes-and-orgs.ttl` | Not published online. Copied from the CIDS repo, `validation/shacl-validation/cache/cids-codes-and-orgs.ttl` (commit `3cb0f3c`, 2026-02-02). That commit is on the `CI-validation` branch, not on `main`. |

`cids-codes-and-orgs.ttl` declares the code classes (`cids:Sector`, `cids:Locality`, ...) as subclasses of `cids:Code`, and defines the organizations that codelists point to with `definedBy` (Common Approach, ESDC, GIIN).

## Corrections to the published shapes

The files above are the published files, unchanged. The Essential and Full tier files have bugs that make every capsule fail, and one of them can't even be loaded. So when the tools load the shapes, they correct these bugs in memory ([`cidsconformance/shape_fixes.py`](../cidsconformance/shape_fixes.py)). Every correction follows the shape's own CIDS annotations (`csh:cardinality`, `csh:in`), so it restores what the shape says it means rather than adding a new rule. The Basic tier and SFF files need no corrections; a test checks that this stays true after a refresh.

| Bug | Essential | Full | Example | Correction |
|---|---|---|---|---|
| "Zero or more" written as "none allowed": `csh:cardinality csh:ZeroOrMore` with `sh:maxCount 0` | 55 | 240 | `Indicator.forOutcome`: no Indicator may link to an Outcome | Drop `sh:maxCount 0` |
| Enumeration with an empty `sh:datatype` (a blank node with nothing in it) | 3 | 27 | `Stakeholder.hasCatchmentArea`: no value can pass | Drop it; check the values listed in `csh:in` with `sh:in` |
| A datatype used as a class: `sh:class xsd:string` with `sh:nodeKind sh:IRI` | 0 | 16 | `Organization.hasPurpose`, `hasWebAddress`, `StakeholderReport` dates | Make it `sh:datatype` with `sh:nodeKind sh:Literal` |
| `sh:class` pointing at an empty blank node | 0 | 1 | `FinancialInput.hasAmount`: no value can pass | Drop it (`sh:nodeKind sh:IRI` still applies) |
| A property shape with two `sh:path` values (not valid SHACL; pyshacl refuses to load the file) | 0 | 1 | `Person_hasAddress_PropertyShape` (`cids:hasAddress` and `ic:hasAddress`) | Split into one shape per path |

Three Full tier shapes (`hasType` on FinancialInput, PhysicalInput and SkillInput) carry two contradictory cardinality annotations (ExactlyOne and ZeroOrMore) and two min/max counts. After the correction they require exactly one value.

(The tools report 241 `max-count-zero` corrections for the Full tier, not 240: splitting `Person_hasAddress` creates a copy of that shape, and the copy is corrected too.)

`python scripts/jena_crosscheck.py` runs Jena with the same corrected shapes. These bugs should be fixed in the published files. Once they are, a refresh will show zero corrections and the test will say so.

## Refreshing

```sh
python -m cidsconformance refresh-reference          # overwrite reference/
python -m cidsconformance suite                      # check nothing broke
```

To try the latest files without changing `reference/`:

```sh
python -m cidsconformance refresh-reference --dest /tmp/cids-reference
CIDS_REFERENCE_DIR=/tmp/cids-reference python -m cidsconformance suite
```

If you refresh, update the date above in the same commit.
