#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONNECTOR_JAR="$ROOT/connector/target/connector.jar"
LOG_DIR="$ROOT/target/logs"
PID_DIR="$ROOT/target/pids"
CONFIG_DIR="$ROOT/target/configuration"

mkdir -p "$LOG_DIR" "$PID_DIR" "$CONFIG_DIR"

cleanup() {
  for pid_file in "$PID_DIR"/*.pid; do
    [[ -f "$pid_file" ]] || continue
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT

wait_for_port() {
  local port="$1"
  local name="$2"
  for _ in $(seq 1 80); do
    if (echo >"/dev/tcp/127.0.0.1/$port") >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "Timed out waiting for $name on port $port" >&2
  return 1
}

mvn -q -f "$ROOT/../edc-extension/pom.xml" install
mvn -q -f "$ROOT/connector/pom.xml" package

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$CONFIG_DIR/private.pem" >/dev/null 2>&1
openssl rsa -in "$CONFIG_DIR/private.pem" -pubout -out "$CONFIG_DIR/public.pem" >/dev/null 2>&1
python3 - "$ROOT" "$CONFIG_DIR" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
config_dir = Path(sys.argv[2])
private_key = config_dir.joinpath("private.pem").read_text().replace("\n", "\\n")
public_key = config_dir.joinpath("public.pem").read_text().replace("\n", "\\n")

for name in ("provider", "consumer"):
    source = root / "resources" / "configuration" / f"{name}.properties"
    target = config_dir / f"{name}.properties"
    lines = source.read_text().splitlines()
    lines.append(f"private-key={private_key}")
    lines.append(f"public-key={public_key}")
    target.write_text("\n".join(lines) + "\n")
PY

java -Dedc.fs.config="$CONFIG_DIR/provider.properties" -jar "$CONNECTOR_JAR" \
  >"$LOG_DIR/provider.log" 2>&1 &
echo "$!" >"$PID_DIR/provider.pid"

java -Dedc.fs.config="$CONFIG_DIR/consumer.properties" -jar "$CONNECTOR_JAR" \
  >"$LOG_DIR/consumer.log" 2>&1 &
echo "$!" >"$PID_DIR/consumer.pid"

wait_for_port 19193 provider-management
wait_for_port 29193 consumer-management
wait_for_port 19194 provider-dsp
wait_for_port 29194 consumer-dsp
sleep 2

python3 "$ROOT/scripts/dsp_e2e_client.py" "$ROOT"

echo "DSP E2E verification passed: two EDC connectors completed catalog, contract negotiation, transfer, EDR, and payload retrieval over DSP."
