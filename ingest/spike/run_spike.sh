#!/usr/bin/env bash
# Orchestrate the Airbyte → SingleStore destination spike checks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "== Nudge destination spike =="
echo "See: ingest/spike/DESTINATION_SPIKE.md"
echo

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

export MOCK_MODE="${MOCK_MODE:-true}"

echo "-- Step 1: local_infile check --"
python3 ingest/spike/check_local_infile.py || true
echo

echo "-- Step 2: Path decision --"
if [[ -z "${SINGLESTORE_HOST:-}" || "${MOCK_MODE}" == "true" ]]; then
  echo "No live SingleStore credentials → use Path C (Postgres + pg_to_s2.py)."
  echo "  docker compose up -d postgres"
  echo "  python3 ingest/seed/seed_postgres.py"
  echo "  MOCK_MODE=true python3 ingest/loader/pg_to_s2.py"
else
  echo "Live SingleStore detected."
  echo "  1. Apply enable_local_infile.sql if check failed"
  echo "  2. Configure Airbyte MySQL destination (Path A) — see ingest/airbyte/"
  echo "  3. If Path A fails, try archived destination-singlestore (Path B)"
  echo "  4. Final fallback: Path C loader"
fi

echo
echo "-- Step 3: Airbyte stubs present --"
ls -1 ingest/airbyte/*.yaml ingest/airbyte/*.yml ingest/airbyte/*.json 2>/dev/null || \
  ls -1 ingest/airbyte/ || true

echo
echo "Spike scaffolding ready. Record results in ingest/spike/spike_log.md after a live run."
