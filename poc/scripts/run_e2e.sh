#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDC_JAR="$ROOT/edc-extension/target/odrl-kr-edc-extension-0.1.0-SNAPSHOT.jar"

cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

"$ROOT/.venv/bin/python" -m pip install -q -r "$ROOT/requirements-dev.txt"

PYTHONPATH="$ROOT/src" "$ROOT/.venv/bin/python" -m pytest \
  tests/test_rdf_shacl_validation.py \
  tests/test_legal_basis_record_schema.py \
  tests/test_legal_basis_record_semantics.py \
  tests/test_s1_decision_trace.py

mvn -q -f "$ROOT/edc-extension/pom.xml" clean package

jar tf "$EDC_JAR" | grep -q 'META-INF/services/org.eclipse.edc.spi.system.ServiceExtension'
jar tf "$EDC_JAR" | grep -q 'org/odrlkr/edc/KoreaPolicyExtension.class'
jar tf "$EDC_JAR" | grep -q 'org/odrlkr/edc/LegalBasisPermissionFunction.class'
jar tf "$EDC_JAR" | grep -q 'org/odrlkr/edc/PseudonymizationDutyFunction.class'
jar tf "$EDC_JAR" | grep -q 'org/odrlkr/edc/SafeAreaPermissionFunction.class'
jar tf "$EDC_JAR" | grep -q 'org/odrlkr/edc/ReferenceLawProhibitionFunction.class'

echo "E2E verification passed: S1 artifacts validated, EDC extension built, service descriptor packaged."
