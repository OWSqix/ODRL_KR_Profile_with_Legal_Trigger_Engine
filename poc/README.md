# ODRL-KR Consent Management Proof Background

This repository is a research proof-of-concept supplement for ODRL-KR, LegalBasisRecord, S1 decision tracing, and EDC 0.16.0-style policy evaluation tests.

It is not legal advice, not compliance certification, and not endorsed by any government body, PIPC, W3C, Eclipse Foundation, or standards organization. The `https://w3id.org/odrl-kr` identifiers are proposed research identifiers until a redirect/governance process is completed.

## Contents

- `ontology/odrl-kr.ttl` - proposed ODRL-KR vocabulary.
- `context/odrl-kr.context.jsonld` - local JSON-LD context for examples.
- `shapes/odrl-kr.shacl.ttl` - manuscript S-1 through S-5 validation rules.
- `schemas/legal-basis-record.schema.json` - LegalBasisRecord JSON Schema.
- `examples/legal-basis-record/` - valid and invalid S1 records.
- `examples/s1-decision-trace/` - S1 input, expected trace, and policy.
- `src/odrl_kr/lte.py` - deterministic S1 LTE trace generator.
- `edc-extension/` - Maven-built EDC 0.16.0 `ServiceExtension` and policy-function tests.
- `docs/proof-background.md` - claim-to-evidence map for manuscript support.

## Run Tests

From `poc/`:

```bash
scripts/run_all_tests.sh
scripts/run_e2e.sh
```

The Java lane is executed through Maven via the local `gradlew` compatibility entrypoint because this workspace has JDK 17 and Maven but no system Gradle. The EDC extension compiles against Eclipse EDC 0.16.0 `policy-engine-spi`, `policy-engine-lib`, `policy-model`, `boot-spi`, and `runtime-metamodel`; see `docs/edc-extension.md`.

For connector-level DSP verification, run from the repository root:

```bash
poc/e2e-dsp/scripts/run_dsp_e2e.sh
```

That script builds a shaded EDC connector runtime, starts provider and consumer connectors, seeds the provider via Management API, fetches the catalog from the consumer, and verifies contract negotiation reaches `FINALIZED`.

## Public Release Boundary

This repository is suitable as a local proof background and GitHub-public research supplement after legal-source verification is completed. It must not be presented as legal advice, regulatory approval, certification, or evidence of official DID operation by any Korean authority.
