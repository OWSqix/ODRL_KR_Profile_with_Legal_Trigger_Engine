import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validator():
    schema = load_json("schemas/legal-basis-record.schema.json")
    return jsonschema.Draft202012Validator(schema)


def test_s1_valid_legal_basis_record_passes_schema():
    errors = sorted(
        validator().iter_errors(load_json("examples/legal-basis-record/s1-valid.json")),
        key=lambda error: list(error.path),
    )
    assert errors == []


def test_s1_invalid_transfer_right_fails_schema():
    errors = list(
        validator().iter_errors(
            load_json("examples/legal-basis-record/s1-invalid-transfer-right.json")
        )
    )
    assert errors
    assert any("False was expected" in error.message for error in errors)


def test_s1_valid_record_contains_manuscript_provisions():
    subject = load_json("examples/legal-basis-record/s1-valid.json")["credentialSubject"]
    assert subject["sourcePersonalDataBasis"]["pseudonymizedDataProcessingBasis"] == "kr:PIPA-28-2"
    assert subject["sourcePersonalDataBasis"]["rightsExclusionBasisForPseudonymizedData"] == "kr:PIPA-28-7"
    assert "kr:PIPA-28-4" in subject["applicableProvisions"]["sectoralObligations"]
    assert "kr:PIPA-28-5" in subject["applicableProvisions"]["prohibitionRules"]
    assert subject["koreaExtension"]["transferRight"]["applicable"] is False
