# SMJ v4 Concept-Proof Validation

Validation date: 2026-04-22

## Verdict

SMJ v4's concept-proof scope is substantially complete for the S1 proof path and exceeds the paper's design-stage validation target by running an actual local two-connector EDC DSP flow through catalog, contract negotiation, transfer, EDR, and payload retrieval.

## Evidence Matrix

| SMJ v4 item | Paper location | PoC evidence | Status |
| --- | --- | --- | --- |
| ODRL-KR vocabulary classifies Korean legal provisions and keeps §23/§28-5/§28-7 out of `dpv:LegalBasis`. | `draft_v2/smj_v4/smj_submission_kr.md:190-264` | `poc/ontology/odrl-kr.ttl`; `tests/test_rdf_shacl_validation.py`; `tests/test_profile_static.py` | PASS |
| ODRL-KR JSON-LD expansion and RDF validation are executable with local context. | `draft_v2/smj_v4/smj_submission_kr.md:437-443` | `poc/context/odrl-kr.context.jsonld`; `test_local_jsonld_context_expands_odrl_kr_terms`; `pyshacl` validation | PASS |
| SHACL S-1 through S-5 are enforced. | `draft_v2/smj_v4/smj_submission_kr.md:437-443` | `poc/shapes/odrl-kr.shacl.ttl`; positive and negative SHACL tests | PASS |
| LegalBasisRecord schema separates pseudonymized-data legal basis from consent flows. | `draft_v2/smj_v4/smj_submission_kr.md:306-323` | `poc/schemas/legal-basis-record.schema.json`; valid/invalid examples; semantic negative tests | PASS |
| S1 decision trace exists for review supplement. | `draft_v2/smj_v4/smj_submission_kr.md:421` | `poc/examples/s1-decision-trace/expected.trace.json`; `src/odrl_kr/lte.py`; trace equality tests | PASS |
| LTE S1 classification yields §28-2, §28-4, §28-5, §28-7. | `draft_v2/smj_v4/smj_submission_kr.md:423-433` | `test_s1_trace_has_required_proof_path` | PASS |
| Conflict trace expectations are represented for S1. | `draft_v2/smj_v4/smj_submission_kr.md:449-461` | S1 trace records Tier 1/Tier 2 not-applicable path; S1 schema-level §28-7 separation is tested | PASS for S1 |
| EDC PolicyEngine extension compiles against EDC 0.16.0. | `draft_v2/smj_v4/smj_submission_kr.md:357-395` | `poc/edc-extension/pom.xml`; `KoreaPolicyExtension`; Maven tests | PASS |
| EDC allow/block policy checks execute. | `draft_v2/smj_v4/smj_submission_kr.md:470-477` | EDC `PolicyEngineImpl` tests: legal basis allow/block, pseudonymization rank, safe-area, re-identification prohibition | PASS |
| Connector-level DSP runtime evidence exists. | PoC-stage extension of `draft_v2/smj_v4/smj_submission_kr.md:421, 477` | `poc/e2e-dsp/scripts/run_dsp_e2e.sh` starts two EDC connectors and reaches `FINALIZED` negotiation, transfer `STARTED`, EDR, payload retrieval | PASS, beyond paper scope |
| VC Data Integrity proof verification. | `draft_v2/smj_v4/smj_submission_kr.md:447, 476` | Schema includes proof object and docs define scope; cryptographic VC proof verification is not implemented | PARTIAL / NOT REQUIRED FOR S1 design-stage proof |
| S1-S6 full scenario implementation. | `draft_v2/smj_v4/smj_submission_kr.md:470-472` | S1 is executable; S2-S6 remain specified but not implemented as full traces/tests | PARTIAL / PoC extension target |

## Commands Re-run

```bash
poc/scripts/run_all_tests.sh
poc/e2e-dsp/scripts/run_dsp_e2e.sh
python3 -m compileall -q poc/src poc/tests poc/e2e-dsp/scripts
git diff --check
```

Observed results:

- `poc/scripts/run_all_tests.sh`: `29 passed`
- `poc/e2e-dsp/scripts/run_dsp_e2e.sh`: contract negotiation `FINALIZED`, transfer `STARTED`, EDR token present, protected payload retrieval succeeded
- `compileall`: pass
- `git diff --check`: pass

## Residual Gaps

These do not block SMJ v4 concept-proof completion, but remain future work:

- Full S2-S6 executable traces and connector tests.
- Real VC Data Integrity cryptographic proof verification.
- Production-grade data-plane hardening, observability, persistence, and security review.
- Formal status propagation bounds and CI-preservation proof.

## Conclusion

For SMJ v4's stated design-stage validation and S1 supplementary proof path, the concept proof is complete. The current PoC also provides stronger-than-paper runtime evidence by executing a local EDC 0.16.0 two-connector DSP flow through negotiation, transfer, EDR, and payload retrieval.
