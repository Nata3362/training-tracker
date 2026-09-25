#!/usr/bin/env bash
# Start the database, backend and frontend in Docker. Code changes reload
# automatically. Stop everything with Ctrl+C.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
docker compose up --build
