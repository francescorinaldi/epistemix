"""Tests for semantic graph analysis (v3 Phase 3).

Replaces citation_graph with typed semantic relations: SUPPORTS, CONTESTS,
CONTRADICTS, CITES, EXTENDS, SUPERVISES, COAUTHORS, TRANSLATES.
"""

from epistemix.models import (
    Anomaly,
    GapType,
    RelationType,
    SemanticRelation,
    Severity,
)


# ============================================================
# TestSemanticGraphBasic
# ============================================================

class TestSemanticGraphBasic:
    """add_relations creates nodes, updates degrees, tracks languages."""

    def test_import(self):
        from epistemix.semantic_graph import SemanticGraph, ScholarNode, AcademicSchool
        assert SemanticGraph is not None
        assert ScholarNode is not None
        assert AcademicSchool is not None

    def test_add_relations_creates_nodes(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="Alice cites Bob",
                language="en",
            ),
        ])
        assert "alice" in g.nodes
        assert "bob" in g.nodes

    def test_add_relations_updates_degrees(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Carol", target="Bob",
                relation=RelationType.CITES,
                confidence=0.8, evidence="cites", language="fr",
            ),
        ])
        assert g.nodes["alice"].out_degree == 1
        assert g.nodes["bob"].in_degree == 2
        assert g.nodes["carol"].out_degree == 1

    def test_add_relations_tracks_languages(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Alice", target="Carol",
                relation=RelationType.SUPPORTS,
                confidence=0.8, evidence="supports", language="fr",
            ),
        ])
        assert "en" in g.nodes["alice"].languages_seen_in
        assert "fr" in g.nodes["alice"].languages_seen_in

    def test_case_insensitive_keys(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="ALICE", target="bob",
                relation=RelationType.SUPPORTS,
                confidence=0.8, evidence="supports", language="fr",
            ),
        ])
        # Should be same node, not two separate nodes
        assert len([k for k in g.nodes if k.startswith("alice") or k.startswith("ALICE")]) == 1
        assert g.nodes["alice"].out_degree == 2

    def test_summary_returns_correct_stats(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Carol",
                relation=RelationType.SUPPORTS,
                confidence=0.8, evidence="supports", language="en",
            ),
        ])
        s = g.summary()
        assert s["total_nodes"] == 3
        assert s["total_relations"] == 2
        assert "schools" in s
        assert "fractures" in s
        assert "isolated_scholars" in s
        assert "relation_types" in s

    def test_typed_adjacency_populated(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.8, evidence="supports", language="en",
            ),
        ])
        adj = g._typed_adjacency
        assert "alice" in adj
        assert "bob" in adj["alice"]
        assert RelationType.CITES in adj["alice"]["bob"]
        assert RelationType.SUPPORTS in adj["alice"]["bob"]

    def test_scholar_node_priority(self):
        from epistemix.semantic_graph import ScholarNode
        node = ScholarNode(name="Alice", in_degree=6, out_degree=2)
        assert node.priority == 6 / (2 + 1)  # 2.0

    def test_scholar_node_priority_investigated(self):
        from epistemix.semantic_graph import ScholarNode
        node = ScholarNode(name="Alice", in_degree=6, out_degree=2, investigated=True)
        assert node.priority == 0.0

    def test_preserves_original_name(self):
        """The node name should preserve original casing."""
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Katerina Peristeri", target="Michalis Lefantzis",
                relation=RelationType.COAUTHORS,
                confidence=0.95, evidence="co-authored", language="en",
            ),
        ])
        assert g.nodes["katerina peristeri"].name == "Katerina Peristeri"


# ============================================================
# TestSchoolDetection
# ============================================================

class TestSchoolDetection:
    """Union-find on SUPPORTS relations."""

    def test_mutual_supports_forms_school(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Alice",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        schools = g.detect_schools()
        assert len(schools) >= 1
        assert schools[0].size >= 2
        members = schools[0].members
        assert "alice" in members
        assert "bob" in members

    def test_no_school_without_supports(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Alice",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
        ])
        schools = g.detect_schools()
        assert len(schools) == 0

    def test_transitive_supports_same_school(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Carol",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        schools = g.detect_schools()
        assert len(schools) >= 1
        # All three should be in the same school
        assert schools[0].size == 3

    def test_schools_sorted_by_size_descending(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        # School 1: Alice, Bob (size 2)
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            # School 2: Carol, Dave, Eve (size 3)
            SemanticRelation(
                source="Carol", target="Dave",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Dave", target="Eve",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        schools = g.detect_schools()
        assert len(schools) == 2
        assert schools[0].size >= schools[1].size

    def test_one_way_supports_still_forms_school(self):
        """SUPPORTS is union-find based, so one-way A->B is enough to link."""
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        schools = g.detect_schools()
        assert len(schools) == 1
        assert schools[0].size == 2


# ============================================================
# TestFractureDetection
# ============================================================

class TestFractureDetection:
    """CONTESTS/CONTRADICTS pairs."""

    def test_contests_is_fracture(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CONTESTS,
                confidence=0.9, evidence="contests", language="en",
            ),
        ])
        fractures = g.detect_fractures()
        assert len(fractures) == 1
        pair = fractures[0]
        assert "alice" in pair and "bob" in pair

    def test_contradicts_is_fracture(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CONTRADICTS,
                confidence=0.9, evidence="contradicts", language="en",
            ),
        ])
        fractures = g.detect_fractures()
        assert len(fractures) == 1

    def test_cites_not_a_fracture(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
        ])
        fractures = g.detect_fractures()
        assert len(fractures) == 0

    def test_deduplicates_fracture_pairs(self):
        """(Alice, Bob) and (Bob, Alice) should be one fracture."""
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CONTESTS,
                confidence=0.9, evidence="contests", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Alice",
                relation=RelationType.CONTRADICTS,
                confidence=0.9, evidence="contradicts", language="en",
            ),
        ])
        fractures = g.detect_fractures()
        assert len(fractures) == 1


# ============================================================
# TestAuthorityDetection
# ============================================================

class TestAuthorityDetection:
    """High CITES in-degree."""

    def test_five_cites_is_authority(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        relations = [
            SemanticRelation(
                source=f"Author{i}", target="BigScholar",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            )
            for i in range(5)
        ]
        g.add_relations(relations)
        authorities = g.detect_authority(min_cites=3)
        names = [a.name for a in authorities]
        assert "BigScholar" in names

    def test_one_cite_not_authority(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
        ])
        authorities = g.detect_authority(min_cites=3)
        assert len(authorities) == 0

    def test_authority_sorted_by_in_degree(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        # BigScholar gets 5 CITES, MediumScholar gets 3
        relations = []
        for i in range(5):
            relations.append(SemanticRelation(
                source=f"Author{i}", target="BigScholar",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ))
        for i in range(3):
            relations.append(SemanticRelation(
                source=f"Other{i}", target="MediumScholar",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ))
        g.add_relations(relations)
        authorities = g.detect_authority(min_cites=3)
        assert len(authorities) == 2
        assert authorities[0].name == "BigScholar"
        assert authorities[1].name == "MediumScholar"

    def test_supports_not_counted_as_cites(self):
        """SUPPORTS should not count toward CITES authority."""
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        relations = [
            SemanticRelation(
                source=f"Author{i}", target="Supporter",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            )
            for i in range(5)
        ]
        g.add_relations(relations)
        authorities = g.detect_authority(min_cites=3)
        assert len(authorities) == 0


# ============================================================
# TestIsolatedDetection
# ============================================================

class TestIsolatedDetection:
    """Nodes with no relations at all."""

    def test_node_with_no_relations_is_isolated(self):
        from epistemix.semantic_graph import SemanticGraph, ScholarNode
        g = SemanticGraph()
        # Manually add a node that has no relations
        g.nodes["lonely"] = ScholarNode(name="Lonely")
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
        ])
        isolated = g.detect_isolated()
        names = [n.name for n in isolated]
        assert "Lonely" in names

    def test_connected_node_not_isolated(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
        ])
        isolated = g.detect_isolated()
        names = [n.name for n in isolated]
        assert "Alice" not in names
        assert "Bob" not in names


# ============================================================
# TestInfluenceChains
# ============================================================

class TestInfluenceChains:
    """SUPERVISES/EXTENDS paths."""

    def test_supervises_extends_chain(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Mentor", target="Student",
                relation=RelationType.SUPERVISES,
                confidence=0.9, evidence="supervises", language="en",
            ),
            SemanticRelation(
                source="Student", target="GradStudent",
                relation=RelationType.EXTENDS,
                confidence=0.9, evidence="extends", language="en",
            ),
        ])
        chains = g.detect_influence_chains(min_length=2)
        assert len(chains) >= 1
        # Should contain a chain of length 3 (3 nodes, 2 edges)
        long_chains = [c for c in chains if len(c) >= 3]
        assert len(long_chains) >= 1

    def test_below_min_length_no_chain(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Mentor", target="Student",
                relation=RelationType.SUPERVISES,
                confidence=0.9, evidence="supervises", language="en",
            ),
        ])
        chains = g.detect_influence_chains(min_length=3)
        assert len(chains) == 0

    def test_cites_not_counted_in_chains(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Mentor", target="Student",
                relation=RelationType.SUPERVISES,
                confidence=0.9, evidence="supervises", language="en",
            ),
            SemanticRelation(
                source="Student", target="Other",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
        ])
        chains = g.detect_influence_chains(min_length=2)
        # No chain of length >= 2 because CITES breaks the path
        long_chains = [c for c in chains if len(c) >= 3]
        assert len(long_chains) == 0

    def test_long_influence_chain(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="A", target="B",
                relation=RelationType.SUPERVISES,
                confidence=0.9, evidence="supervises", language="en",
            ),
            SemanticRelation(
                source="B", target="C",
                relation=RelationType.EXTENDS,
                confidence=0.9, evidence="extends", language="en",
            ),
            SemanticRelation(
                source="C", target="D",
                relation=RelationType.SUPERVISES,
                confidence=0.9, evidence="supervises", language="en",
            ),
        ])
        chains = g.detect_influence_chains(min_length=2)
        # Should find A->B->C->D chain
        assert any(len(c) == 4 for c in chains)


# ============================================================
# TestUnmappedPairs
# ============================================================

class TestUnmappedPairs:
    """Entities with no relation between them."""

    def test_entities_without_relation_are_unmapped(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        # 4 entities. Alice<->Bob related. Carol<->Dave related.
        # Alice and Carol both have >= 2 mentions but NO relation.
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Alice",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Carol", target="Dave",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Dave", target="Carol",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        # Alice: in=1 out=1 => 2; Bob: in=1 out=1 => 2
        # Carol: in=1 out=1 => 2; Dave: in=1 out=1 => 2
        # Related: Alice-Bob, Carol-Dave
        # Unmapped: Alice-Carol, Alice-Dave, Bob-Carol, Bob-Dave
        unmapped = g.detect_unmapped_pairs(min_mentions=2)
        pair_sets = [frozenset(p) for p in unmapped]
        assert frozenset(("alice", "carol")) in pair_sets
        assert frozenset(("alice", "dave")) in pair_sets
        assert frozenset(("bob", "carol")) in pair_sets
        assert frozenset(("bob", "dave")) in pair_sets
        # Related pairs should NOT be in unmapped
        assert frozenset(("alice", "bob")) not in pair_sets
        assert frozenset(("carol", "dave")) not in pair_sets

    def test_related_entities_not_unmapped(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        # Create enough relations so both Alice and Bob have >= 2 mentions
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Alice",
                relation=RelationType.SUPPORTS,
                confidence=0.8, evidence="supports", language="en",
            ),
        ])
        # Alice and Bob both have 2 mentions and ARE related
        unmapped = g.detect_unmapped_pairs(min_mentions=2)
        pair_sets = [frozenset(p) for p in unmapped]
        assert frozenset(("alice", "bob")) not in pair_sets


# ============================================================
# TestAnomalyGeneration
# ============================================================

class TestAnomalyGeneration:
    """Combine all detectors into anomalies."""

    def test_fracture_generates_fracture_line_anomaly(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CONTESTS,
                confidence=0.9, evidence="contests", language="en",
            ),
        ])
        anomalies = g.generate_anomalies()
        fracture_anomalies = [
            a for a in anomalies if a.gap_type == GapType.FRACTURE_LINE
        ]
        assert len(fracture_anomalies) >= 1
        assert fracture_anomalies[0].severity == Severity.MEDIUM

    def test_high_citation_uninvestigated_generates_citation_island(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        relations = [
            SemanticRelation(
                source=f"Author{i}", target="MysteryScholar",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            )
            for i in range(5)
        ]
        g.add_relations(relations)
        # MysteryScholar has 5 CITES in-degree and is not investigated
        anomalies = g.generate_anomalies()
        citation_anomalies = [
            a for a in anomalies if a.gap_type == GapType.CITATION_ISLAND
        ]
        assert len(citation_anomalies) >= 1
        assert citation_anomalies[0].severity == Severity.HIGH

    def test_single_school_generates_school_gap(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        # Create one school of size 3
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Carol",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        schools = g.detect_schools()
        assert len(schools) == 1
        assert schools[0].size >= 3
        anomalies = g.generate_anomalies()
        school_anomalies = [
            a for a in anomalies if a.gap_type == GapType.SCHOOL_GAP
        ]
        assert len(school_anomalies) >= 1
        assert school_anomalies[0].severity == Severity.CRITICAL

    def test_two_schools_no_school_gap(self):
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        g.add_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Bob", target="Carol",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            # Second school
            SemanticRelation(
                source="Dave", target="Eve",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
            SemanticRelation(
                source="Eve", target="Frank",
                relation=RelationType.SUPPORTS,
                confidence=0.9, evidence="supports", language="en",
            ),
        ])
        anomalies = g.generate_anomalies()
        school_anomalies = [
            a for a in anomalies if a.gap_type == GapType.SCHOOL_GAP
        ]
        assert len(school_anomalies) == 0

    def test_investigated_authority_no_citation_island(self):
        """If the highly-cited scholar IS investigated, no anomaly."""
        from epistemix.semantic_graph import SemanticGraph
        g = SemanticGraph()
        relations = [
            SemanticRelation(
                source=f"Author{i}", target="KnownScholar",
                relation=RelationType.CITES,
                confidence=0.9, evidence="cites", language="en",
            )
            for i in range(5)
        ]
        g.add_relations(relations)
        g.nodes["knownscholar"].investigated = True
        anomalies = g.generate_anomalies()
        citation_anomalies = [
            a for a in anomalies if a.gap_type == GapType.CITATION_ISLAND
        ]
        assert len(citation_anomalies) == 0
