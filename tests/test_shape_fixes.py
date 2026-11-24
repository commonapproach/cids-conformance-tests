"""The corrections to the published shapes (cidsconformance/shape_fixes.py)."""

from collections import Counter

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection

from cidsconformance.reference import published_shapes_graph, shape_corrections, shapes_graph
from cidsconformance.shape_fixes import correct_shapes

SH = Namespace("http://www.w3.org/ns/shacl#")
CSH = Namespace("https://ontology.commonapproach.org/cids/shacl#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")


def test_basic_and_sff_shapes_need_no_corrections():
    # If a refresh changes this, the corrections now touch results the
    # suite relied on: review them before accepting the new files.
    assert shape_corrections("basic") == []
    assert shape_corrections("sff") == []


def test_tier_corrections_are_the_known_ones():
    # Pinned to the files retrieved on 2026-11-24 (reference/SOURCES.md).
    assert Counter(c.kind for c in shape_corrections("essential")) == {"max-count-zero": 55, "empty-datatype": 3}
    assert Counter(c.kind for c in shape_corrections("full")) == {
        "max-count-zero": 241, "empty-datatype": 27, "datatype-as-class": 16,
        "empty-class": 1, "multiple-paths": 1,
    }


def test_corrections_are_deterministic():
    runs = {tuple(sorted(map(str, shape_corrections("full")))) for _ in range(3)}
    assert len(runs) == 1


def test_published_graph_is_left_unchanged():
    published = published_shapes_graph("essential")
    assert len(published) != len(shapes_graph("essential"))
    assert any(int(m) == 0 for m in published.objects(None, SH.maxCount))


def test_corrected_shapes_have_no_remaining_bugs():
    for profile in ("essential", "full"):
        g = shapes_graph(profile)
        assert correct_shapes(g) == []        # a second pass finds nothing
        for s in set(g.subjects(SH.path, None)):
            assert len(set(g.objects(s, SH.path))) == 1


def _shape(*triples) -> Graph:
    g = Graph()
    s = URIRef("urn:test:shape")
    for p, o in triples:
        g.add((s, p, o))
    return g


def test_max_count_zero_is_dropped_only_for_open_ended_properties():
    open_ended = _shape((SH.path, URIRef("urn:p")), (SH.maxCount, Literal(0)), (CSH.cardinality, CSH.ZeroOrMore))
    correct_shapes(open_ended)
    assert not list(open_ended.objects(None, SH.maxCount))

    forbidden = _shape((SH.path, URIRef("urn:p")), (SH.maxCount, Literal(0)), (CSH.cardinality, CSH.ExactlyOne))
    assert correct_shapes(forbidden) == []
    assert list(forbidden.objects(None, SH.maxCount)) == [Literal(0)]


def test_empty_datatype_becomes_sh_in_from_csh_in():
    from rdflib import BNode
    g = _shape((SH.path, URIRef("urn:p")), (SH.datatype, BNode()),
               (CSH["in"], Literal("local")), (CSH["in"], Literal("global")))
    correct_shapes(g)
    s = URIRef("urn:test:shape")
    assert g.value(s, SH.datatype) is None
    assert sorted(Collection(g, g.value(s, SH["in"]))) == [Literal("global"), Literal("local")]


def test_datatype_used_as_class_becomes_a_datatype():
    g = _shape((SH.path, URIRef("urn:p")), (SH["class"], XSD.string), (SH.nodeKind, SH.IRI))
    correct_shapes(g)
    s = URIRef("urn:test:shape")
    assert g.value(s, SH["class"]) is None
    assert g.value(s, SH.datatype) == XSD.string
    assert g.value(s, SH.nodeKind) == SH.Literal
