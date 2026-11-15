#!/usr/bin/env bash
# ==============================================================================
# OS-SimBench: Automated Test Harness (Phase 4 Reliability Verification)
# Runs full test suite (CPU, Memory, Deadlock, Disk, and Boundary Cases)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_BIN="python"
fi

echo "=================================================================="
echo "          Running OS-SimBench Comprehensive Unit & Boundary Tests"
echo "=================================================================="

$PYTHON_BIN "$SCRIPT_DIR/main.py" --test
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "=================================================================="
    echo " [TEST STATUS: PASSED] All unit & reliability tests passed cleanly."
    echo "=================================================================="
else
    echo "=================================================================="
    echo " [TEST STATUS: FAILED] Some tests encountered errors (Exit code $EXIT_CODE)."
    echo "=================================================================="
fi

exit $EXIT_CODE
