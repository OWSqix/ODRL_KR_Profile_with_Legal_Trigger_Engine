from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_docs_contain_non_legal_advice_and_non_endorsement_language():
    required_docs = [
        "README.md",
        "NOTICE",
        "docs/public-release-disclaimer.md",
    ]
    for path in required_docs:
        text = read(path).lower()
        assert "not legal advice" in text
        assert "not endorsed" in text or "no endorsement" in text


def test_proof_background_maps_claims_to_tests():
    text = read("docs/proof-background.md")
    required = [
        "ODRL-KR",
        "LegalBasisRecord",
        "S1",
        "tests/test_profile_static.py",
        "tests/test_legal_basis_record_schema.py",
        "tests/test_s1_decision_trace.py",
        "KoreaPolicyFunctionTest.java",
    ]
    for item in required:
        assert item in text


def test_edc_docs_state_adapter_boundary():
    text = read("docs/edc-extension.md")
    assert "Eclipse EDC 0.16.0 artifacts" in text
    assert "ServiceExtension" in text
    assert "AtomicConstraintRuleFunction" in text
    assert "production EDC connector" in text
