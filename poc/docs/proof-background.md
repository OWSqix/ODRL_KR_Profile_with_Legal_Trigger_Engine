# Proof Background

This document maps manuscript claims to executable or inspectable proof artifacts.

| Manuscript claim | Evidence file | Test |
| --- | --- | --- |
| ODRL-KR has first-class Korean legal-provision terms and separates lawful bases from condition/prohibition/rights-exclusion rules. | `ontology/odrl-kr.ttl` | `tests/test_profile_static.py::test_required_profile_terms_are_declared`, `tests/test_profile_static.py::test_non_basis_provisions_are_not_dpv_legal_basis` |
| Pseudonymization level comparison uses integer rank semantics. | `ontology/odrl-kr.ttl`, `templates/pipa-28-2-pseudonymized-research.ttl` | `tests/test_profile_static.py::test_pseudonymization_rank_uses_integer_ordering`, Java `pseudonymizationRankAllowsLevelTwoAndBlocksLevelOne` |
| S1 LegalBasisRecord separates source basis, applicable provisions, and Korea extension fields. | `schemas/legal-basis-record.schema.json`, `examples/legal-basis-record/s1-valid.json` | `tests/test_legal_basis_record_schema.py::test_s1_valid_legal_basis_record_passes_schema` |
| PIPA Section 28-7 excludes transfer-right applicability for S1 pseudonymized-data flow. | `examples/legal-basis-record/s1-valid.json`, `examples/legal-basis-record/s1-invalid-transfer-right.json` | `tests/test_legal_basis_record_schema.py::test_s1_invalid_transfer_right_fails_schema` |
| LTE derives S1 candidate provisions and decision trace from asset metadata. | `src/odrl_kr/lte.py`, `examples/s1-decision-trace/expected.trace.json` | `tests/test_s1_decision_trace.py::test_s1_lte_trace_matches_expected_fixture` |
| EDC 0.16.0 policy functions compile and run against actual EDC SPI/model artifacts. | `edc-extension/pom.xml`, `edc-extension/src/main/java/org/odrlkr/edc/KoreaPolicyExtension.java` | Maven `edc-extension` tests in `KoreaPolicyFunctionTest.java` |
| EDC runtime checks allow safe-area use and block re-identification for S1. | `edc-extension/src/main/java/org/odrlkr/edc/*Function.java` | `edc-extension/src/test/java/org/odrlkr/edc/KoreaPolicyFunctionTest.java` |
| Two EDC connectors can complete DSP catalog, contract negotiation, transfer, EDR, and payload retrieval. | `e2e-dsp/` | `e2e-dsp/scripts/run_dsp_e2e.sh` |

## Release Safety

The proof background supports a research claim that the manuscript concepts can be represented and tested against ODRL-KR RDF/SHACL artifacts, JSON Schema, deterministic LTE traces, and Eclipse EDC 0.16.0 policy-extension APIs. It does not prove legal compliance, government approval, production security, or full connector deployment conformance.
