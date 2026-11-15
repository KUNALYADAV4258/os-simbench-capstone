#!/usr/bin/env bash
# ==============================================================================
# OS-SimBench: Main Launcher Script for Ubuntu 24.04 LTS / WSL2
# Course: ENSC-351 Operating Systems Laboratory
# ==============================================================================

set -e

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo "          OS-SimBench: OS Resource Management Simulator"
echo "          Environment: Ubuntu / WSL2 / Python 3.x"
echo "=================================================================="

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3 (sudo apt install python3 python3-pip)."
    exit 1
fi

PYTHON_BIN="python3"
echo "[OK] Found $($PYTHON_BIN --version)"

# Check virtual environment or requirements
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "[INFO] Activating existing virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
    PYTHON_BIN="python"
fi

# Ensure output directories exist
mkdir -p "$SCRIPT_DIR/reports/charts"
mkdir -p "$SCRIPT_DIR/reports/logs"

# Execute application with passed arguments or launch menu
exec $PYTHON_BIN "$SCRIPT_DIR/main.py" "$@"
