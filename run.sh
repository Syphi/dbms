#!/usr/bin/env bash
# Run the DBMS CLI from the project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="${SCRIPT_DIR}" python "${SCRIPT_DIR}/src/main.py" "$@"
