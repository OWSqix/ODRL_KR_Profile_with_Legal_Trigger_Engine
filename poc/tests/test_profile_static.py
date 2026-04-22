from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_profile_terms_are_declared():
    ttl = read("ontology/odrl-kr.ttl")
    required_terms = [
        "kr:PIPA-15",
        "kr:PIPA-17",
        "kr:PIPA-23",
        "kr:PIPA-28-2",
        "kr:PIPA-28-4",
        "kr:PIPA-28-5",
        "kr:PIPA-28-7",
        "kr:PIPA-28-8",
        "kr:PIPA-35-2",
        "kr:legalBasisOperand",
        "kr:purposeOperand",
        "kr:pseudonymizationLevel",
        "kr:referenceLaw",
        "kr:pseudonymize",
        "kr:process-in-safe-area",
        "kr:re-identify",
    ]
    for term in required_terms:
        assert term in ttl


def test_non_basis_provisions_are_not_dpv_legal_basis():
    ttl = read("ontology/odrl-kr.ttl")
    assert "kr:PIPA-23 a kr:SpecialCategoryCondition ." in ttl
    assert "kr:PIPA-28-5 a kr:ProhibitionRule ." in ttl
    assert "kr:PIPA-28-7 a kr:RightsExclusionRule ." in ttl
    assert "kr:PIPA-23 a kr:LawfulProcessingBasis, dpv:LegalBasis" not in ttl
    assert "kr:PIPA-28-5 a kr:LawfulProcessingBasis, dpv:LegalBasis" not in ttl
    assert "kr:PIPA-28-7 a kr:LawfulProcessingBasis, dpv:LegalBasis" not in ttl


def test_pseudonymization_rank_uses_integer_ordering():
    ttl = read("ontology/odrl-kr.ttl")
    assert "kr:rank a rdf:Property ; rdfs:range xsd:integer ." in ttl
    assert "kr:Pseudonymization-Level-2 a kr:PseudonymizationLevel ; kr:rank 2 ." in ttl


def test_s1_template_declares_profile_and_runtime_controls():
    template = read("templates/pipa-28-2-pseudonymized-research.ttl")
    assert "odrl:profile <https://w3id.org/odrl-kr>" in template
    assert "odrl:rightOperand kr:PIPA-28-2" in template
    assert "odrl:action kr:process-in-safe-area" in template
    assert "odrl:action kr:re-identify" in template


def test_s4_shape_scopes_rank_check_to_pseudonymization_operand():
    shapes = read("shapes/odrl-kr.shacl.ttl")
    assert "sh:targetObjectsOf odrl:rightOperand" not in shapes
    assert "sh:targetSubjectsOf odrl:leftOperand" in shapes
    assert "$this odrl:leftOperand kr:pseudonymizationLevel" in shapes
    assert "FILTER NOT EXISTS { ?level kr:rank ?rank . }" in shapes


def test_s4_shape_does_not_rank_check_non_pseudonymization_operands():
    template = read("templates/pipa-28-2-pseudonymized-research.ttl")
    shapes = read("shapes/odrl-kr.shacl.ttl")
    non_rank_right_operands = [
        "odrl:rightOperand kr:PIPA-28-2",
        "odrl:rightOperand dpv:ResearchAndDevelopment",
        "odrl:rightOperand true",
        "odrl:rightOperand kr:PIPA-28-5",
    ]
    for operand in non_rank_right_operands:
        assert operand in template
    assert "sh:targetObjectsOf odrl:rightOperand" not in shapes
