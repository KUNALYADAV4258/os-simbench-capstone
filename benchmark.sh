#!/usr/bin/env bash
# ==============================================================================
# OS-SimBench: Automated Batch Benchmark Suite Runner
# Executes complete comparative benchmarks across CPU, Memory, Deadlock, Disk.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo "          Starting OS-SimBench Automated Benchmarks..."
echo "=================================================================="

PYTHON_BIN="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_BIN="python"
fi

# Run python benchmark mode
$PYTHON_BIN "$SCRIPT_DIR/main.py" --benchmark

echo ""
echo "=================================================================="
echo " [OK] Benchmarks Complete!"
echo " Verification of Output Artifacts:"
echo "=================================================================="
ls -lh "$SCRIPT_DIR/reports/charts"

echo ""
echo "Simulation Activity Log:"
tail -n 8 "$SCRIPT_DIR/reports/logs/sim_activity.log"
echo "=================================================================="
