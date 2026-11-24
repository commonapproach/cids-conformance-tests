"""Corrections for known bugs in the published CIDS SHACL shapes.

The pinned files in ``reference/shacl/`` are the published files, unchanged.
These corrections are applied in memory when the shapes are loaded. Each one
is mechanical: it follows the shape's own CIDS annotations
(``csh:cardinality``, ``csh:in``), so it restores what the shape says it
means rather than adding new rules.

As of 2026-11, only the Essential and Full tier files need correcting. The
Basic tier and SFF files need none (``tests/test_shape_fixes.py`` checks
this, so a refresh that changes it is noticed).

The bugs:

1. **"Zero or more" written as "none allowed".** Property shapes annotated
   ``csh:cardinality csh:ZeroOrMore`` (or ``csh:OneOrMore``) have
   ``sh:maxCount 0``, which forbids the property entirely. Even an
   Indicator's ``forOutcome`` fails. Fix: drop the ``sh:maxCount 0``.
2. **Enumerations with an empty datatype.** Properties with a fixed list of
   values (``hasCatchmentArea``, ``hasLikelihood``, ...) have
   ``sh:datatype`` pointing at an empty blank node, so no value can pass.
   The allowed values are in ``csh:in``. Fix: drop the empty datatype and
   check the values with ``sh:in`` instead.
3. **Empty class.** ``FinancialInput.hasAmount`` has ``sh:class`` pointing
   at an empty blank node, so no value can pass. There is no annotation
   saying what was meant. Fix: drop it (``sh:nodeKind sh:IRI`` still
   applies).
4. **A property shape with two paths.** ``Person_hasAddress_PropertyShape``
   in the Full tier has two ``sh:path`` values. That isn't valid SHACL, and
   pyshacl refuses to load the file. Fix: split it into one property shape
   per path.
5. **A datatype used as a class.** Some literal properties
   (``Organization.hasPurpose``, ``hasWebAddress``, ``StakeholderReport``
   dates ...) have ``sh:class xsd:string`` (or another XSD type) with
   ``sh:nodeKind sh:IRI``, so no literal can pass. Fix: make it
   ``sh:datatype`` with ``sh:nodeKind sh:Literal``.
"""

from __future__ import annotations

from dataclasses import dataclass

from rdflib import BNode, Graph, Literal, Namespace, URIRef, XSD
from rdflib.collection import Collection

SH = Namespace("http://www.w3.org/ns/shacl#")
CSH = Namespace("https://ontology.commonapproach.org/cids/shacl#")

OPEN_ENDED = {CSH.ZeroOrMore, CSH.OneOrMore}


@dataclass(frozen=True)
class Correction:
    kind: str       # "max-count-zero" | "empty-datatype" | "empty-class" | "multiple-paths" | "datatype-as-class"
    shape: str      # IRI of the property shape that was corrected

    def __str__(self) -> str:
        return f"{self.kind}: {self.shape}"


def _is_empty_bnode(g: Graph, node) -> bool:
    return isinstance(node, BNode) and next(iter(g.predicate_objects(node)), None) is None


def correct_shapes(g: Graph) -> list[Correction]:
    """Correct ``g`` in place and return what was changed."""
    done: list[Correction] = []

    # 4. Split property shapes that have more than one sh:path.
    for shape in sorted({s for s in g.subjects(SH.path, None) if len(set(g.objects(s, SH.path))) > 1}):
        paths = sorted(g.objects(shape, SH.path))
        others = [(p, o) for p, o in g.predicate_objects(shape) if p != SH.path]
        parents = list(g.subjects(SH.property, shape))
        for i, path in enumerate(paths[1:], start=2):
            copy = URIRef(f"{shape}__path{i}")
            g.add((copy, SH.path, path))
            for p, o in others:
                g.add((copy, p, o))
            for parent in parents:
                g.add((parent, SH.property, copy))
        for path in paths[1:]:
            g.remove((shape, SH.path, path))
        done.append(Correction("multiple-paths", str(shape)))

    # 1. sh:maxCount 0 on properties that are meant to be open-ended.
    # (Three Full tier shapes, hasType on FinancialInput/PhysicalInput/
    # SkillInput, carry two cardinality annotations, ExactlyOne and
    # ZeroOrMore, plus two minCounts and two maxCounts. Checking every
    # annotation keeps this deterministic; they end up as exactly one.)
    for shape in sorted(set(g.subjects(SH.maxCount, None))):
        if any(int(m) == 0 for m in g.objects(shape, SH.maxCount)) and \
                any(c in OPEN_ENDED for c in g.objects(shape, CSH.cardinality)):
            for m in list(g.objects(shape, SH.maxCount)):
                if int(m) == 0:
                    g.remove((shape, SH.maxCount, m))
            done.append(Correction("max-count-zero", str(shape)))

    # 2. sh:datatype pointing at an empty blank node: use csh:in instead.
    for shape, dt in sorted(g.subject_objects(SH.datatype)):
        if not _is_empty_bnode(g, dt):
            continue
        g.remove((shape, SH.datatype, dt))
        allowed = sorted(o for o in g.objects(shape, CSH["in"]) if isinstance(o, Literal))
        if allowed:
            head = BNode()
            Collection(g, head, [Literal(str(v)) for v in allowed])
            g.add((shape, SH["in"], head))
        done.append(Correction("empty-datatype", str(shape)))

    # 3. sh:class pointing at an empty blank node.
    for shape, cls in sorted(g.subject_objects(SH["class"])):
        if _is_empty_bnode(g, cls):
            g.remove((shape, SH["class"], cls))
            done.append(Correction("empty-class", str(shape)))

    # 5. An XSD datatype used as sh:class.
    for shape, cls in sorted(g.subject_objects(SH["class"])):
        if isinstance(cls, URIRef) and str(cls).startswith(str(XSD)):
            g.remove((shape, SH["class"], cls))
            g.add((shape, SH.datatype, cls))
            if (shape, SH.nodeKind, SH.IRI) in g:
                g.remove((shape, SH.nodeKind, SH.IRI))
                g.add((shape, SH.nodeKind, SH.Literal))
            done.append(Correction("datatype-as-class", str(shape)))

    return done


def corrected(g: Graph) -> tuple[Graph, list[Correction]]:
    """A corrected copy of ``g``; ``g`` itself is left alone."""
    out = Graph()
    for prefix, ns in g.namespaces():
        out.bind(prefix, ns, override=True, replace=True)
    for t in g:
        out.add(t)
    return out, correct_shapes(out)


__all__ = ["Correction", "correct_shapes", "corrected"]
