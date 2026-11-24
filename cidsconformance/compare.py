"""Compare an exported capsule with the capsule that was imported.

The comparison is done on the RDF graph, so JSON-LD layout, key order,
context style, nesting, and Turtle vs JSON-LD don't matter. Blank nodes (such
as the i72:Measure behind each IndicatorReport value) are matched by content.

Besides a plain triple diff, the tool explains the common round-trip
failures:

* IRI_CHANGED       a node came back under a different IRI
* DUPLICATE_NODE    one node came back as two or more nodes
                    (e.g. an Indicator linked to two Outcomes exported twice)
* PREDICATE_CHANGED same value, different property (e.g. cids:hasComment
                    came back as sff:hasComment)
* VALUE_CHANGED     same property, different value
* LITERAL_REFORMATTED same value written differently (e.g. a dateTime in
                    another time zone). Allowed unless --strict.
* MISSING_NODE / MISSING_TRIPLE / EXTRA_NODE / EXTRA_TRIPLE
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field

from rdflib import BNode, Graph, Literal, RDF, URIRef
from rdflib.compare import to_canonical_graph

from .shacl import describe_node, qname

FAILING_KINDS = {
    "IRI_CHANGED",
    "DUPLICATE_NODE",
    "PREDICATE_CHANGED",
    "VALUE_CHANGED",
    "MISSING_NODE",
    "MISSING_TRIPLE",
}
EXTRA_KINDS = {"EXTRA_NODE", "EXTRA_TRIPLE"}
LENIENT_KINDS = {"LITERAL_REFORMATTED"}


@dataclass(frozen=True, order=True)
class Difference:
    kind: str
    node: str
    path: str = ""
    imported: str = ""
    exported: str = ""
    value: str = ""       # PREDICATE_CHANGED: the value that moved to the other property

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        bits = [f"{self.kind:<20} {self.node}"]
        if self.path:
            bits.append(f"  {self.path}")
        if self.imported or self.exported:
            bits.append(f"  imported: {self.imported or '(none)'}  exported: {self.exported or '(none)'}")
        if self.value:
            bits.append(f"  value: {self.value}")
        return "".join(bits)


@dataclass
class ComparisonReport:
    differences: list[Difference] = field(default_factory=list)
    strict: bool = False
    allow_extra: bool = False
    imported_triples: int = 0
    exported_triples: int = 0

    def failing(self) -> list[Difference]:
        kinds = set(FAILING_KINDS)
        if not self.allow_extra:
            kinds |= EXTRA_KINDS
        if self.strict:
            kinds |= LENIENT_KINDS
        return [d for d in self.differences if d.kind in kinds]

    @property
    def passed(self) -> bool:
        return not self.failing()

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "strict": self.strict,
            "allow_extra": self.allow_extra,
            "imported_triples": self.imported_triples,
            "exported_triples": self.exported_triples,
            "counts": dict(Counter(d.kind for d in self.differences)),
            "differences": [d.to_dict() for d in self.differences],
        }

    def to_text(self) -> str:
        lines = [
            f"Imported: {self.imported_triples} triples   Exported: {self.exported_triples} triples",
        ]
        if not self.differences:
            lines.append("No differences: the export matches the import.")
        else:
            failing = set(self.failing())
            for kind, n in sorted(Counter(d.kind for d in self.differences).items()):
                lines.append(f"  {kind}: {n}")
            lines.append("")
            for d in self.differences:
                marker = "FAIL" if d in failing else "warn"
                lines.append(f"[{marker}] {d}")
        lines.append("")
        lines.append("RESULT: PASS" if self.passed else "RESULT: FAIL")
        return "\n".join(lines)


def _fmt(term) -> str:
    if isinstance(term, Literal):
        dt = f"^^{qname(term.datatype)}" if term.datatype else ""
        lang = f"@{term.language}" if term.language else ""
        return f'"{term}"{lang}{dt}'
    return qname(term) if isinstance(term, URIRef) else str(term)


def _signature(g: Graph, node) -> tuple | None:
    """Types plus literal-valued properties. Links to other nodes are left out,
    so a node keeps its signature even if its links were split up or rewired."""
    types = frozenset(g.objects(node, RDF.type))
    literals = frozenset((p, o) for p, o in g.predicate_objects(node) if isinstance(o, Literal))
    if not literals:
        return None  # too little to go on
    return (types, literals)


def _iri_subjects(g: Graph) -> set:
    return {s for s in g.subjects() if isinstance(s, URIRef)}


def _rename(g: Graph, mapping: dict) -> Graph:
    out = Graph()
    for s, p, o in g:
        out.add((mapping.get(s, s), p, mapping.get(o, o)))
    return out


def _match_nodes(imported: Graph, exported: Graph):
    """Find IRIs that were re-minted, and nodes that were duplicated."""
    imp_subjects = _iri_subjects(imported)
    exp_subjects = _iri_subjects(exported)

    imp_by_sig = defaultdict(list)
    for s in imp_subjects:
        sig = _signature(imported, s)
        if sig is not None:
            imp_by_sig[sig].append(s)

    new_by_sig = defaultdict(list)
    for s in exp_subjects - imp_subjects:
        sig = _signature(exported, s)
        if sig is not None:
            new_by_sig[sig].append(s)

    renamed, duplicated = {}, {}
    for sig, originals in imp_by_sig.items():
        if len(originals) != 1:
            continue  # ambiguous: several imported nodes look the same
        original = originals[0]
        newcomers = sorted(new_by_sig.get(sig, []), key=str)
        if not newcomers:
            continue
        if original in exp_subjects:
            for n in newcomers:
                duplicated[n] = original
        elif len(newcomers) == 1:
            renamed[newcomers[0]] = original
        else:
            renamed[newcomers[0]] = original
            for n in newcomers[1:]:
                duplicated[n] = original
    return renamed, duplicated


def compare_graphs(
    imported: Graph,
    exported: Graph,
    strict: bool = False,
    allow_extra: bool = False,
    ignore_predicates: tuple[str, ...] = (),
) -> ComparisonReport:
    ignore = {URIRef(p) for p in ignore_predicates}
    if ignore:
        imported = _without(imported, ignore)
        exported = _without(exported, ignore)

    report = ComparisonReport(
        strict=strict,
        allow_extra=allow_extra,
        imported_triples=len(imported),
        exported_triples=len(exported),
    )
    diffs: list[Difference] = []

    renamed, duplicated = _match_nodes(imported, exported)
    for new, old in sorted(renamed.items(), key=lambda kv: str(kv[1])):
        diffs.append(Difference("IRI_CHANGED", str(old), "", str(old), str(new)))
    for dup, original in sorted(duplicated.items(), key=lambda kv: (str(kv[1]), str(kv[0]))):
        diffs.append(Difference("DUPLICATE_NODE", str(original), "", str(original), str(dup)))

    # Fold renamed/duplicated nodes back onto the original IRI so the
    # remaining diff shows what else changed, not the same problem 20 times.
    exported_mapped = _rename(exported, {**renamed, **duplicated})

    ci = to_canonical_graph(imported)
    ce = to_canonical_graph(exported_mapped)
    missing = set(ci) - set(ce)
    extra = set(ce) - set(ci)

    diffs.extend(_explain(ci, ce, missing, extra))
    report.differences = sorted(set(diffs), key=lambda d: (d.kind not in FAILING_KINDS, d.kind, d.node, d.path, d.imported, d.exported))
    return report


def _without(g: Graph, predicates: set) -> Graph:
    out = Graph()
    for t in g:
        if t[1] not in predicates:
            out.add(t)
    return out


def _explain(ci: Graph, ce: Graph, missing: set, extra: set) -> list[Difference]:
    diffs = []
    missing, extra = set(missing), set(extra)

    def node_name(g, s):
        return describe_node(g, s)

    # Bnode-subject triples hang off a parent (e.g. a Measure under a report).
    # Name them by parent so imported/exported versions pair up.
    def key_sp(g, s, p):
        return (node_name(g, s), p)

    # 0. Triples that only differ because a blank node got a new canonical
    #    label (its content changed elsewhere) are not differences themselves.
    extra_by_key = defaultdict(list)
    for t in extra:
        extra_by_key[(node_name(ce, t[0]), t[1], _obj_key(ce, t[2]))].append(t)
    for t in sorted(missing, key=str):
        cands = extra_by_key.get((node_name(ci, t[0]), t[1], _obj_key(ci, t[2])))
        if cands:
            missing.discard(t)
            extra.discard(cands.pop(0))

    # 1. Same subject + object, different predicate.
    extra_by_so = defaultdict(list)
    for t in extra:
        extra_by_so[(node_name(ce, t[0]), _obj_key(ce, t[2]))].append(t)
    for t in sorted(missing, key=str):
        cands = [e for e in extra_by_so.get((node_name(ci, t[0]), _obj_key(ci, t[2])), [])
                 if e in extra and e[1] != t[1]]
        if cands:
            e = cands[0]
            missing.discard(t)
            extra.discard(e)
            diffs.append(Difference("PREDICATE_CHANGED", node_name(ci, t[0]), "",
                                    qname(t[1]), qname(e[1]), _obj_text(ci, t[2])))

    # 2. Same subject + predicate, different object.
    miss_by_sp = defaultdict(list)
    for t in missing:
        miss_by_sp[key_sp(ci, t[0], t[1])].append(t)
    extra_by_sp = defaultdict(list)
    for t in extra:
        extra_by_sp[key_sp(ce, t[0], t[1])].append(t)
    for k in sorted(set(miss_by_sp) & set(extra_by_sp), key=str):
        ms, es = miss_by_sp[k], extra_by_sp[k]
        if isinstance(ms[0][2], BNode) or isinstance(es[0][2], BNode):
            continue  # changes inside the blank node are reported below
        # Pair value-equal literals first (reformatting), then 1:1 leftovers.
        for m in list(ms):
            for e in list(es):
                if isinstance(m[2], Literal) and isinstance(e[2], Literal) and _same_value(m[2], e[2]):
                    ms.remove(m); es.remove(e)
                    missing.discard(m); extra.discard(e)
                    diffs.append(Difference("LITERAL_REFORMATTED", k[0], qname(k[1]), _fmt(m[2]), _fmt(e[2])))
                    break
        if len(ms) == 1 and len(es) == 1:
            m, e = ms[0], es[0]
            missing.discard(m); extra.discard(e)
            diffs.append(Difference("VALUE_CHANGED", k[0], qname(k[1]), _fmt(m[2]), _fmt(e[2])))

    # 3. Whatever is left. Whole nodes missing/added are reported once.
    def whole_nodes(triples, g):
        by_s = defaultdict(set)
        for t in triples:
            by_s[t[0]].add(t)
        return {s for s, ts in by_s.items() if isinstance(s, URIRef) and len(ts) == len(set(g.triples((s, None, None))))}

    missing_nodes = whole_nodes(missing, ci) - set(ce.subjects())
    extra_nodes = whole_nodes(extra, ce) - set(ci.subjects())
    for s in missing_nodes:
        diffs.append(Difference("MISSING_NODE", str(s), "", _types(ci, s), ""))
    for s in extra_nodes:
        diffs.append(Difference("EXTRA_NODE", str(s), "", "", _types(ce, s)))
    for t in missing:
        if t[0] in missing_nodes or _is_bnode_inside(ci, t, missing):
            continue
        diffs.append(Difference("MISSING_TRIPLE", node_name(ci, t[0]), qname(t[1]), _obj_text(ci, t[2]), ""))
    for t in extra:
        if t[0] in extra_nodes or _is_bnode_inside(ce, t, extra):
            continue
        diffs.append(Difference("EXTRA_TRIPLE", node_name(ce, t[0]), qname(t[1]), "", _obj_text(ce, t[2])))
    return diffs


def _types(g: Graph, s) -> str:
    return ", ".join(sorted(qname(t) for t in g.objects(s, RDF.type))) or "(untyped)"


def _obj_key(g: Graph, o):
    return describe_node(g, o) if isinstance(o, BNode) else o


def _obj_text(g: Graph, o) -> str:
    if isinstance(o, BNode):
        inner = "; ".join(sorted(f"{qname(p)} {_fmt(v)}" for p, v in g.predicate_objects(o)))
        return f"[ {inner} ]"
    return _fmt(o)


def _is_bnode_inside(g: Graph, t, bucket: set) -> bool:
    """A triple whose subject is a blank node that is itself reported as a
    whole object of another triple in the same bucket."""
    s = t[0]
    if not isinstance(s, BNode):
        return False
    return any(o == s for (_s, _p, o) in bucket)


def _same_value(a: Literal, b: Literal) -> bool:
    if a.datatype != b.datatype:
        return False
    try:
        return a.eq(b) and a.toPython() == b.toPython()
    except Exception:
        return False
