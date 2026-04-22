# Verification Report

Generated for the `poc/` proof-of-concept after hardening ontology and EDC extension validation.

## External API / Standard Basis

- EDC policy engine documentation: policy functions implement `AtomicConstraintRuleFunction<R extends Rule, C extends PolicyContext>` and evaluate operator/rightOperand/rule/context tuples.
- EDC extension documentation: custom features are contributed as EDC extensions and loaded via `META-INF/services/org.eclipse.edc.spi.system.ServiceExtension`.
- Maven Central artifacts pinned by `poc/edc-extension/pom.xml`:
  - `org.eclipse.edc:policy-engine-spi:0.16.0`
  - `org.eclipse.edc:policy-engine-lib:0.16.0`
  - `org.eclipse.edc:policy-model:0.16.0`
  - `org.eclipse.edc:boot-spi:0.16.0`
  - `org.eclipse.edc:runtime-metamodel:0.16.0`

## Commands Verified

```bash
poc/scripts/run_all_tests.sh
poc/scripts/run_e2e.sh
poc/e2e-dsp/scripts/run_dsp_e2e.sh
mvn -f poc/edc-extension/pom.xml test
mvn -q -f poc/edc-extension/pom.xml package -DskipTests
jar tf poc/edc-extension/target/odrl-kr-edc-extension-0.1.0-SNAPSHOT.jar
mvn -f poc/edc-extension/pom.xml dependency:tree -Dincludes=org.eclipse.edc
python3 -m compileall -q poc/src poc/tests
git diff --check
```

## Latest Observed Results

- Python/RDF/SHACL/JSON Schema/LTE/docs tests: `29 passed`.
- Maven EDC extension tests: `Tests run: 10, Failures: 0, Errors: 0, Skipped: 0`.
- E2E script verifies S1 artifacts, builds the EDC extension JAR, and checks packaged service descriptor/classes.
- DSP E2E starts two actual EDC connector runtimes, seeds provider asset/policy/contract definition, fetches provider catalog from the consumer, verifies contract negotiation reaches `FINALIZED`, starts transfer, retrieves EDR, rejects unauthenticated/invalid-token payload access, and fetches the protected payload with the EDR token.
- Latest DSP E2E output observed:
  - `datasetId`: `s1-broadcast-viewing-log`
  - `state`: `FINALIZED`
  - `transferState`: `STARTED`
  - `payloadBytes`: `5645`
  - missing token rejected with `401`
  - invalid token rejected with `403`
  - `DSP E2E verification passed: two EDC connectors completed catalog, contract negotiation, transfer, EDR, and payload retrieval over DSP.`
- Maven EDC build: `BUILD SUCCESS`.
- Packaged JAR contains `META-INF/services/org.eclipse.edc.spi.system.ServiceExtension` and `org/odrlkr/edc/KoreaPolicyExtension.class`.
- EDC dependency tree confirms all EDC artifacts are pinned to `0.16.0`.
- `compileall` passed.
- `git diff --check` passed.

## Remaining Non-Claims

This PoC does not claim legal correctness, PIPC/government endorsement, production security, or operational readiness. It proves that the manuscript's S1 policy/background can be represented, validated, executed against pinned EDC 0.16.0 policy-extension APIs, packaged into an EDC connector runtime, and exercised through a local two-connector DSP catalog, contract-negotiation, transfer, EDR, and payload-retrieval flow.
