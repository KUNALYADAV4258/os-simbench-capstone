#!/usr/bin/env bash
# ==============================================================================
# OS-SimBench: Linux Kernel System Diagnostic Probe
# Inspects real Linux OS kernel telemetry to bridge simulations with real systems.
# ==============================================================================

echo "=================================================================="
echo "          OS-SimBench Linux Kernel Diagnostic Probe"
echo "=================================================================="

# Check Linux /proc availability
if [ ! -d "/proc" ]; then
    echo "[INFO] Running on non-Linux host. /proc filesystem not directly mounted."
    echo "Tip: Run inside Ubuntu 24.04 LTS (WSL2) to inspect active Linux kernel metrics."
    exit 0
fi

echo "--- CPU Architecture & Cores ---"
grep "model name" /proc/cpuinfo | head -n 2 || true
echo "Total CPU Cores: $(grep -c "processor" /proc/cpuinfo || echo 1)"

echo ""
echo "--- Memory Management Telemetry (/proc/meminfo) ---"
grep -E "(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree)" /proc/meminfo || true

echo ""
echo "--- Storage Devices (/proc/partitions) ---"
cat /proc/partitions || true

echo ""
echo "--- Context Switches & CPU Ticks (/proc/stat) ---"
grep "ctxt" /proc/stat || true
grep "processes" /proc/stat || true

echo "=================================================================="
echo " [OK] System diagnostic probe completed successfully."
echo "=================================================================="
