#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_FILE="${ROOT_DIR}/scripts/chartdb-schema.sql"
OUTPUT_FILE="${1:-${ROOT_DIR}/docs/chartdb/schema.json}"

cd "$ROOT_DIR"

if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
fi

if [ ! -f "$SQL_FILE" ]; then
    echo "ChartDB SQL file not found: $SQL_FILE" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

if ! docker compose ps --status running db --format '{{.Name}}' | grep -q .; then
    echo "Database container is not running. Start it with: docker compose up -d db" >&2
    exit 1
fi

DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-app}"
TMP_FILE="$(mktemp)"

cleanup() {
    rm -f "$TMP_FILE"
}
trap cleanup EXIT

docker compose exec -T db psql \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -tA \
    -f - < "$SQL_FILE" > "$TMP_FILE"

python3 -m json.tool "$TMP_FILE" > "$OUTPUT_FILE"

echo "ChartDB schema written to ${OUTPUT_FILE}"
