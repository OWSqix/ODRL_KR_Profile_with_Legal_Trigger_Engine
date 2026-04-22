#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

"$ROOT/.venv/bin/python" -m pip install -q -r "$ROOT/requirements-dev.txt"
PYTHONPATH="$ROOT/src" "$ROOT/.venv/bin/python" -m pytest tests
./gradlew -p edc-extension test

echo "All ODRL-KR proof-background tests passed."
