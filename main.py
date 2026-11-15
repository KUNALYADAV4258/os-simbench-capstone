"""
Main Application Entry Point for OS-SimBench.
Course: ENSC-351 Operating Systems Laboratory
Provides an integrated CLI, interactive menu, and batch benchmarking harness.
"""

import os
import sys
import json
import argparse
import unittest
from typing import List, Dict, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sim.pcb import Process, ProcessState
from sim.cpu_scheduler import CPUScheduler
from sim.memory_manager import MemoryManager
from sim.deadlock import DeadlockManager
from sim.disk_scheduler import DiskScheduler
from sim.visualizer import Visualizer
from sim.logger import setup_logger, get_sim_logger

def load_json_file(rel_path: str) -> Dict[str, Any]:
    full_path = os.path.join(BASE_DIR, rel_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------
# Module 1: CPU Scheduling Handler
# ---------------------------------------------------------------------
def run_cpu_module(interactive: bool = True, workload_name: str = "standard_workload"):
    print("\n" + "="*60)
    print(" [MODULE 1] CPU SCHEDULING SIMULATION")
    print("="*60)

    workloads = load_json_file("data/cpu_workloads.json")
    if interactive:
        print("\nAvailable Workloads:")
        for idx, k in enumerate(workloads.keys(), 1):
            print(f"  {idx}. {k}")
        choice = input("Select workload (default 1): ").strip()
        keys = list(workloads.keys())
        key = keys[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(keys) else keys[0]
    else:
        key = workload_name if workload_name in workloads else "standard_workload"

    procs_data = workloads[key]
    processes = [
        Process(
            pid=p["pid"],
            arrival_time=p["arrival_time"],
            burst_time=p["burst_time"],
            priority=p.get("priority", 0)
        )
        for p in procs_data
    ]

    print(f"\nLoaded Workload: '{key}' ({len(processes)} processes)")
    headers = ["PID", "Arrival Time", "Burst Time", "Priority"]
    rows = [[p.pid, p.arrival_time, p.burst_time, p.priority] for p in processes]
    print(Visualizer.render_table(headers, rows, "Input Process Table"))

    scheduler = CPUScheduler()
    results = [
        scheduler.schedule_fcfs(processes),
        scheduler.schedule_sjf(processes),
        scheduler.schedule_srtf(processes),
        scheduler.schedule_priority(processes),
        scheduler.schedule_priority_preemptive(processes),
        scheduler.schedule_round_robin(processes, quantum=2),
        scheduler.schedule_mlfq(processes, q0_quantum=2, q1_quantum=4, aging_interval=15)
    ]

    summary_headers = ["Algorithm", "Total Time", "Idle", "CPU Util %", "Avg TAT", "Avg WT", "Avg RT", "Throughput"]
    summary_rows = [
        [r.algorithm_name, r.total_time, r.idle_time, f"{r.cpu_utilization:.1f}%",
         f"{r.avg_turnaround_time:.2f}", f"{r.avg_waiting_time:.2f}", f"{r.avg_response_time:.2f}", f"{r.throughput:.4f}"]
        for r in results
    ]
    print(Visualizer.render_table(summary_headers, summary_rows, "Comparative Scheduling Performance"))

    # Print sample Gantt Chart for the best performing scheduler (lowest WT)
    best_res = min(results, key=lambda x: x.avg_waiting_time)
    print(f"\nOptimal Scheduler for this workload: {best_res.algorithm_name}")
    print(Visualizer.render_ascii_gantt(best_res.gantt_chart))

    # Save visual charts
    chart_path = os.path.join(BASE_DIR, "reports", "charts", "cpu_comparison.png")
    gantt_path = os.path.join(BASE_DIR, "reports", "charts", "cpu_best_gantt.png")
    Visualizer.plot_cpu_comparison(results, chart_path)
    Visualizer.plot_cpu_gantt(best_res.gantt_chart, gantt_path, f"Optimal Schedule ({best_res.algorithm_name})")
    print(f"Saved charts to:\n  - {chart_path}\n  - {gantt_path}")
    return results

# ---------------------------------------------------------------------
# Module 2: Memory Management Handler
# ---------------------------------------------------------------------
def run_memory_module(interactive: bool = True):
    print("\n" + "="*60)
    print(" [MODULE 2] MEMORY MANAGEMENT & PAGE REPLACEMENT")
    print("="*60)

    mem_data = load_json_file("data/memory_traces.json")
    trace_info = mem_data["silberschatz_canonical"]
    ref_string = trace_info["reference_string"]
    num_frames = trace_info["default_frames"]

    print(f"\nPage Reference String: {ref_string}")
    print(f"Allocated Frames: {num_frames}")

    mm = MemoryManager()
    res_fifo = mm.fifo_page_replacement(ref_string, num_frames)
    res_lru = mm.lru_page_replacement(ref_string, num_frames)
    res_opt = mm.optimal_page_replacement(ref_string, num_frames)
    res_clock = mm.clock_page_replacement(ref_string, num_frames)

    results = [res_fifo, res_lru, res_opt, res_clock]
    headers = ["Algorithm", "Frames", "Total References", "Faults", "Hits", "Fault Rate %", "Hit Rate %"]
    rows = [
        [r.algorithm_name, r.num_frames, r.total_references, r.page_faults, r.page_hits, f"{r.fault_rate:.1f}%", f"{r.hit_rate:.1f}%"]
        for r in results
    ]
    print(Visualizer.render_table(headers, rows, "Page Replacement Comparative Results"))

    # Belady's Anomaly Demo
    print("\n--- Testing Belady's Anomaly (FIFO) ---")
    anomaly = mm.check_beladys_anomaly(frame_range=(3, 4))
    print(f"Canonical Trace: {anomaly['reference_string']}")
    print(f"Faults with 3 Frames: {anomaly['faults_by_frame'][3]}")
    print(f"Faults with 4 Frames: {anomaly['faults_by_frame'][4]}")
    if anomaly["anomaly_detected"]:
        print("  ALERT: Belady's Anomaly detected! Increasing frame count increased page faults (9 -> 10)!")

    # Multi-frame curve generation
    curves = {"FIFO": {}, "LRU": {}, "Optimal": {}, "Clock": {}}
    for f in range(2, 7):
        curves["FIFO"][f] = mm.fifo_page_replacement(ref_string, f).page_faults
        curves["LRU"][f] = mm.lru_page_replacement(ref_string, f).page_faults
        curves["Optimal"][f] = mm.optimal_page_replacement(ref_string, f).page_faults
        curves["Clock"][f] = mm.clock_page_replacement(ref_string, f).page_faults

    chart_path = os.path.join(BASE_DIR, "reports", "charts", "page_fault_curves.png")
    Visualizer.plot_page_fault_curves(curves, chart_path)
    print(f"Saved fault curve chart to: {chart_path}")

    # Contiguous Allocation Demo
    print("\n--- Contiguous Allocation Analysis ---")
    contig = mem_data["contiguous_sample"]
    blocks = contig["blocks"]
    procs = contig["processes"]
    print(f"Memory Blocks: {blocks} KB")
    print(f"Process Requests: {procs} KB")

    for algo in ["first_fit", "best_fit", "worst_fit"]:
        alloc_res = mm.allocate_contiguous(blocks, procs, algo)
        print(f"\n[{alloc_res.algorithm_name}]")
        for p, b in alloc_res.allocations.items():
            b_desc = f"Block {b} ({blocks[b]} KB)" if b is not None else "UNALLOCATED"
            print(f"  {p} ({procs[p]} KB) -> {b_desc}")
        print(f"  Internal Frag: {alloc_res.internal_fragmentation} KB | External Frag: {alloc_res.external_fragmentation} KB")

    return results

# ---------------------------------------------------------------------
# Module 3: Deadlock Management Handler
# ---------------------------------------------------------------------
def run_deadlock_module(interactive: bool = True):
    print("\n" + "="*60)
    print(" [MODULE 3] DEADLOCK AVOIDANCE (BANKER'S ALGORITHM)")
    print("="*60)

    data = load_json_file("data/deadlock_scenarios.json")["silberschatz_safe"]
    pids = data["processes"]
    available = data["available"]
    max_m = data["max"]
    alloc = data["allocation"]

    dm = DeadlockManager(pids, available, max_m, alloc)
    print(f"Processes: {pids}")
    print(f"Available Resource Vector: {available}")

    headers = ["Process", "Allocation (A B C)", "Max Claim (A B C)", "Need (A B C)"]
    rows = []
    for i, p in enumerate(pids):
        rows.append([
            p,
            " ".join(map(str, alloc[i])),
            " ".join(map(str, max_m[i])),
            " ".join(map(str, dm.need[i]))
        ])
    print(Visualizer.render_table(headers, rows, "Banker's Initial System State"))

    # Run Safety Algorithm
    safety_res = dm.check_safety()
    print("\nStep-by-step Safety Execution Trace:")
    for step in safety_res.trace:
        print(f"  {step}")

    # Test Resource Request
    req_data = data["sample_request"]
    pid = req_data["pid"]
    req = req_data["request"]
    print(f"\n--- Testing Resource Request: Process {pid} requests {req} ---")
    req_res = dm.request_resources(pid, req)
    print(f"Outcome: {req_res.reason}")

    # Test Unsafe Request
    print(f"\n--- Testing Unsafe Request: Process P0 requests [0, 3, 0] ---")
    unsafe_res = dm.request_resources("P0", [0, 3, 0])
    print(f"Outcome: {unsafe_res.reason}")

    return safety_res

# ---------------------------------------------------------------------
# Module 4: Disk Scheduling Handler
# ---------------------------------------------------------------------
def run_disk_module(interactive: bool = True):
    print("\n" + "="*60)
    print(" [MODULE 4] DISK STORAGE SCHEDULING")
    print("="*60)

    data = load_json_file("data/disk_workloads.json")["silberschatz_sample"]
    requests = data["requests"]
    head = data["initial_head"]
    direction = data["direction"]
    max_cyl = data["max_cylinder"]

    print(f"Initial Head Position: {head}")
    print(f"Request Queue: {requests}")
    print(f"Direction: {direction} | Cylinders: 0 to {max_cyl}")

    ds = DiskScheduler(max_cylinder=max_cyl)
    results = [
        ds.schedule_fcfs(requests, head),
        ds.schedule_sstf(requests, head),
        ds.schedule_scan(requests, head, direction),
        ds.schedule_cscan(requests, head, direction),
        ds.schedule_look(requests, head, direction),
        ds.schedule_clook(requests, head, direction)
    ]

    headers = ["Algorithm", "Initial Head", "Total Head Movement", "Avg Seek", "Seek Path"]
    rows = [
        [r.algorithm_name, r.initial_head, f"{r.total_head_movement} cyl", f"{r.avg_seek_distance:.2f}",
         r.get_summary_dict()["sequence_path"][:45] + "..."]
        for r in results
    ]
    print(Visualizer.render_table(headers, rows, "Disk Scheduling Comparative Performance"))

    best_disk = min(results, key=lambda x: x.total_head_movement)
    print(f"\nOptimal Disk Scheduler: {best_disk.algorithm_name} ({best_disk.total_head_movement} cylinders)")

    chart_path = os.path.join(BASE_DIR, "reports", "charts", "disk_trajectories.png")
    Visualizer.plot_disk_trajectories(results, chart_path)
    print(f"Saved trajectory chart to: {chart_path}")

    return results

# ---------------------------------------------------------------------
# Module 5: Integrated End-to-End Simulation Pipeline
# ---------------------------------------------------------------------
def run_integrated_pipeline():
    print("\n" + "="*60)
    print(" [INTEGRATED PIPELINE] END-TO-END PROCESS LIFECYCLE")
    print("="*60)
    print("Simulating a realistic OS job entering the system:")
    print("1. Process Admission -> 2. Memory Paging Allocation -> 3. Banker's Resource Safety -> 4. CPU Scheduling -> 5. Disk I/O Servicing -> 6. Termination\n")

    p = Process(
        pid="JOB_101",
        arrival_time=0,
        burst_time=6,
        priority=1,
        pages=[2, 4, 1, 2, 5, 2],
        allocated_resources=[1, 0, 1],
        max_resources=[2, 1, 2],
        disk_requests=[45, 120, 85]
    )

    print(f"[Step 1] Created Process PCB: {p.pid} (Burst={p.burst_time}, Pages={p.pages}, Disk I/O={p.disk_requests})")

    # Step 2: Memory allocation
    mm = MemoryManager()
    mem_res = mm.lru_page_replacement(p.pages, num_frames=3)
    print(f"[Step 2] Virtual Memory Management: LRU Allocated 3 Frames. Page Faults: {mem_res.page_faults}, Hits: {mem_res.page_hits}")

    # Step 3: Deadlock check
    dm = DeadlockManager(
        process_ids=[p.pid, "DAEMON_1"],
        available=[2, 2, 1],
        max_matrix=[p.max_resources, [1, 1, 1]],
        allocation_matrix=[p.allocated_resources, [0, 1, 0]]
    )
    safe = dm.check_safety()
    print(f"[Step 3] Resource Allocation Safety: Is Safe? {safe.is_safe} (Sequence: {' -> '.join(safe.safe_sequence)})")

    # Step 4: CPU Dispatch
    sched = CPUScheduler()
    cpu_res = sched.schedule_round_robin([p], quantum=2)
    print(f"[Step 4] CPU Execution: RR (q=2) Slices: {cpu_res.gantt_chart}, Completion Time={p.completion_time}")

    # Step 5: Disk I/O
    ds = DiskScheduler(max_cylinder=199)
    disk_res = ds.schedule_sstf(p.disk_requests, initial_head=50)
    print(f"[Step 5] Disk I/O Servicing: SSTF Serviced {p.disk_requests} in {disk_res.total_head_movement} head movements.")

    print("\n[Step 6] Process TERMINATED successfully. Complete system audit logged to reports/logs/sim_activity.log.")

# ---------------------------------------------------------------------
# Full Benchmark Suite
# ---------------------------------------------------------------------
def run_full_benchmark():
    print("\n" + "#"*65)
    print(" EXECUTING OS-SIMBENCH COMPLETE AUTOMATED BENCHMARK SUITE")
    print("#"*65)
    run_cpu_module(interactive=False)
    run_memory_module(interactive=False)
    run_deadlock_module(interactive=False)
    run_disk_module(interactive=False)
    run_integrated_pipeline()
    print("\n" + "="*65)
    print(" ALL BENCHMARKS COMPLETED SUCCESSFULLY. CHARTS GENERATED IN reports/charts/")
    print("="*65)

# ---------------------------------------------------------------------
# Interactive Menu
# ---------------------------------------------------------------------
def interactive_menu():
    while True:
        print("\n" + "="*50)
        print("          OS-SIMBENCH MAIN MENU")
        print("="*50)
        print(" 1. CPU Scheduling Simulation & Comparison")
        print(" 2. Memory Management (Paging & Allocation)")
        print(" 3. Deadlock Avoidance (Banker's Algorithm)")
        print(" 4. Disk Storage Scheduling & Trajectories")
        print(" 5. Integrated End-to-End OS Pipeline")
        print(" 6. Run Complete Benchmark Suite (Generate Charts)")
        print(" 7. Launch Interactive Web Dashboard")
        print(" 8. Run Unit Tests & Boundary Validations")
        print(" 0. Exit")
        print("="*50)
        choice = input("Enter choice (0-8): ").strip()

        if choice == "1":
            run_cpu_module(interactive=True)
        elif choice == "2":
            run_memory_module(interactive=True)
        elif choice == "3":
            run_deadlock_module(interactive=True)
        elif choice == "4":
            run_disk_module(interactive=True)
        elif choice == "5":
            run_integrated_pipeline()
        elif choice == "6":
            run_full_benchmark()
        elif choice == "7":
            import web_server
            web_server.run_server(port=8080)
        elif choice == "8":
            suite = unittest.defaultTestLoader.discover(os.path.join(BASE_DIR, "tests"))
            unittest.TextTestRunner(verbosity=2).run(suite)
        elif choice == "0":
            print("\nExiting OS-SimBench. Thank you!")
            break
        else:
            print("Invalid selection. Please choose an option from 0 to 8.")

def main():
    parser = argparse.ArgumentParser(description="OS-SimBench: Operating System Resource Management Simulator & Benchmark Suite")
    parser.add_argument("--benchmark", action="store_true", help="Run automated benchmark suite and generate charts")
    parser.add_argument("--test", action="store_true", help="Run unit test suite")
    parser.add_argument("--web", action="store_true", help="Launch interactive web dashboard server")
    parser.add_argument("--port", type=int, default=8080, help="Web server port (default 8080)")
    parser.add_argument("--module", choices=["cpu", "memory", "deadlock", "disk", "pipeline"], help="Run specific subsystem module")
    parser.add_argument("--workload", type=str, default="standard_workload", help="Workload key for CPU module")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()
    setup_logger(log_file=os.path.join(BASE_DIR, "reports", "logs", "sim_activity.log"), verbose=args.verbose)

    if args.web:
        import web_server
        web_server.run_server(port=args.port)
    elif args.benchmark:
        run_full_benchmark()
    elif args.test:
        suite = unittest.defaultTestLoader.discover(os.path.join(BASE_DIR, "tests"))
        res = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(0 if res.wasSuccessful() else 1)
    elif args.module == "cpu":
        run_cpu_module(interactive=False, workload_name=args.workload)
    elif args.module == "memory":
        run_memory_module(interactive=False)
    elif args.module == "deadlock":
        run_deadlock_module(interactive=False)
    elif args.module == "disk":
        run_disk_module(interactive=False)
    elif args.module == "pipeline":
        run_integrated_pipeline()
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
