import copy

import jsonschema

from test_legal_basis_record_schema import load_json, validator


def validation_errors(document):
    return list(validator().iter_errors(document))


def test_legal_basis_record_rejects_consent_receipt_only_revoked_state():
    document = load_json("examples/legal-basis-record/s1-valid.json")
    document = copy.deepcopy(document)
    document["credentialSubject"]["status"] = "revoked"

    errors = validation_errors(document)

    assert errors
    assert any("not one of" in error.message for error in errors)


def test_legal_basis_record_requires_rights_exclusion_basis_for_s1():
    document = load_json("examples/legal-basis-record/s1-valid.json")
    document = copy.deepcopy(document)
    del document["credentialSubject"]["sourcePersonalDataBasis"]["rightsExclusionBasisForPseudonymizedData"]

    errors = validation_errors(document)

    assert errors
    assert any("required property" in error.message for error in errors)


def test_legal_basis_record_rejects_sensitive_condition_as_lawful_basis():
    document = load_json("examples/legal-basis-record/s1-valid.json")
    document = copy.deepcopy(document)
    document["credentialSubject"]["applicableProvisions"]["lawfulProcessingBasis"] = "kr:PIPA-23"

    errors = validation_errors(document)

    assert errors
    assert any("'kr:PIPA-28-2' was expected" in error.message for error in errors)


def test_legal_basis_record_schema_is_draft_2020_12_valid():
    schema = load_json("schemas/legal-basis-record.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
