#!/usr/bin/env bash
# ==============================================================================
# OS-SimBench: Interactive Web Dashboard Launcher for Ubuntu / WSL2
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_BIN="python"
fi

PORT="${1:-8080}"

echo "=================================================================="
echo "          Launching OS-SimBench Web Dashboard"
echo "          Access in your browser: http://localhost:$PORT"
echo "=================================================================="

exec $PYTHON_BIN "$SCRIPT_DIR/web_server.py" "$PORT"
