from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, RDF, URIRef


ROOT = Path(__file__).resolve().parents[1]


def parse_graph(*relative_paths: str) -> Graph:
    graph = Graph()
    for relative_path in relative_paths:
        graph.parse(ROOT / relative_path)
    return graph


def test_odrl_kr_ontology_and_s1_template_pass_shacl_validation():
    data_graph = parse_graph(
        "ontology/odrl-kr.ttl",
        "templates/pipa-28-2-pseudonymized-research.ttl",
    )
    shapes_graph = parse_graph("shapes/odrl-kr.shacl.ttl")

    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        advanced=True,
    )

    assert conforms, report_text
    assert len(report_graph) > 0


def test_s4_shacl_rejects_pseudonymization_constraint_without_rank():
    data_graph = parse_graph("ontology/odrl-kr.ttl")
    data_graph.parse(
        data="""
            @prefix : <https://example.org/invalid/> .
            @prefix odrl: <http://www.w3.org/ns/odrl/2/> .
            @prefix kr: <https://w3id.org/odrl-kr#> .

            :UnrankedLevel a kr:PseudonymizationLevel .

            :InvalidDuty a odrl:Duty ;
                odrl:action kr:pseudonymize ;
                odrl:constraint [
                    odrl:leftOperand kr:pseudonymizationLevel ;
                    odrl:operator odrl:gteq ;
                    odrl:rightOperand :UnrankedLevel
                ] .
        """,
        format="turtle",
    )
    shapes_graph = parse_graph("shapes/odrl-kr.shacl.ttl")

    conforms, _, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        advanced=True,
    )

    assert not conforms
    assert "S-4" in report_text


def test_s5_shacl_rejects_non_basis_provision_typed_as_legal_basis():
    data_graph = parse_graph("ontology/odrl-kr.ttl")
    data_graph.parse(
        data="""
            @prefix kr: <https://w3id.org/odrl-kr#> .
            @prefix dpv: <https://w3id.org/dpv#> .
            kr:PIPA-28-5 a dpv:LegalBasis .
        """,
        format="turtle",
    )
    shapes_graph = parse_graph("shapes/odrl-kr.shacl.ttl")

    conforms, _, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        advanced=True,
    )

    assert not conforms
    assert "S-5" in report_text


def test_s1_template_uses_declared_odrl_kr_terms_only():
    ontology = parse_graph("ontology/odrl-kr.ttl")
    template = parse_graph("templates/pipa-28-2-pseudonymized-research.ttl")
    odrl = "http://www.w3.org/ns/odrl/2/"
    kr_namespace = "https://w3id.org/odrl-kr#"

    referenced_terms = set()
    for predicate in ("leftOperand", "action", "rightOperand"):
        for term in template.objects(None, URIRef(odrl + predicate)):
            if isinstance(term, URIRef) and str(term).startswith(kr_namespace):
                referenced_terms.add(term)

    assert referenced_terms
    for term in referenced_terms:
        assert (term, RDF.type, None) in ontology, f"{term} is used by S1 template but not typed in ontology"


def test_local_jsonld_context_expands_odrl_kr_terms():
    context_uri = (ROOT / "context/odrl-kr.context.jsonld").as_uri()
    graph = Graph()
    graph.parse(
        data=f"""
        {{
          "@context": "{context_uri}",
          "@id": "https://example.org/policy/Test",
          "profile": "https://w3id.org/odrl-kr",
          "target": "kr:Broadcast-Viewing-Log-2027-Q1",
          "action": "kr:process-in-safe-area"
        }}
        """,
        format="json-ld",
    )

    subject = URIRef("https://example.org/policy/Test")
    assert (subject, URIRef("http://www.w3.org/ns/odrl/2/profile"), URIRef("https://w3id.org/odrl-kr")) in graph
    assert (subject, URIRef("http://www.w3.org/ns/odrl/2/action"), URIRef("https://w3id.org/odrl-kr#process-in-safe-area")) in graph


def test_only_lawful_processing_basis_terms_are_dpv_legal_basis():
    ontology = parse_graph("ontology/odrl-kr.ttl")
    dpv_legal_basis = URIRef("https://w3id.org/dpv#LegalBasis")
    lawful_processing_basis = URIRef("https://w3id.org/odrl-kr#LawfulProcessingBasis")

    legal_basis_terms = set(ontology.subjects(RDF.type, dpv_legal_basis))

    assert legal_basis_terms == {
        URIRef("https://w3id.org/odrl-kr#PIPA-15"),
        URIRef("https://w3id.org/odrl-kr#PIPA-17"),
        URIRef("https://w3id.org/odrl-kr#PIPA-28-2"),
    }
    for term in legal_basis_terms:
        assert (term, RDF.type, lawful_processing_basis) in ontology


def test_pseudonymization_levels_have_exact_unique_ranks():
    ontology = parse_graph("ontology/odrl-kr.ttl")
    kr = "https://w3id.org/odrl-kr#"
    rank_predicate = URIRef(kr + "rank")

    ranks = {
        str(level): int(rank)
        for level, rank in ontology.subject_objects(rank_predicate)
        if str(level).startswith(kr + "Pseudonymization-Level-")
    }

    assert ranks == {
        kr + "Pseudonymization-Level-1": 1,
        kr + "Pseudonymization-Level-2": 2,
        kr + "Pseudonymization-Level-3": 3,
    }
    assert len(set(ranks.values())) == 3


def test_odrl_left_operands_are_bound_to_declared_properties():
    ontology = parse_graph("ontology/odrl-kr.ttl")
    kr = "https://w3id.org/odrl-kr#"
    odrl_left_operand = URIRef("http://www.w3.org/ns/odrl/2/LeftOperand")
    refers_to_property = URIRef(kr + "refersToProperty")

    expected_operands = {
        URIRef(kr + "legalBasisOperand"),
        URIRef(kr + "purposeOperand"),
        URIRef(kr + "pseudonymizationLevel"),
        URIRef(kr + "referenceLaw"),
    }
    actual_operands = set(ontology.subjects(RDF.type, odrl_left_operand))

    assert expected_operands.issubset(actual_operands)
    for operand in expected_operands:
        assert (operand, refers_to_property, None) in ontology
