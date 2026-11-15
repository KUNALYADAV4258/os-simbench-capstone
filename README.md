# OS-SimBench: Operating System Resource Management Simulator & Benchmark Suite

**Course:** Operating Systems Laboratory (`ENSC-351`), B.Tech Semester V  
**Target Platform:** Ubuntu 24.04 LTS (WSL2 / Linux), Bash Shell, Python 3.x  
**Submission Category:** Integrated OS Capstone Project (100 Marks)  

### 👥 Project Authors
- **Kunal Yadav** (`2401730157`)
- **Yashasvi Bhagour** (`2401730074`)
- **Vanshika** (`2501732297`)

---

## 📌 Project Overview
`OS-SimBench` is an integrated, modular simulation and benchmarking platform designed to model, test, and analyze the four core pillars of operating system resource management:
1. **Processor Management:** CPU Scheduling (`FCFS`, `SJF`, `SRTF`, `Priority`, `Round Robin`, `MLFQ`).
2. **Memory Management:** Virtual Memory & Page Replacement (`FIFO`, `LRU`, `Optimal`, `Clock`, Belady's Anomaly analysis) + Contiguous Allocation (`First Fit`, `Best Fit`, `Worst Fit`).
3. **Deadlock Management:** Dijkstra's Banker's Algorithm (Safety checks, Resource Request evaluation with automatic rollback) + Wait-For Graph cycle detection.
4. **Secondary Storage Management:** Disk Head Trajectory Scheduling (`FCFS`, `SSTF`, `SCAN`, `C-SCAN`, `LOOK`, `C-LOOK`).
5. **Integrated OS Pipeline:** End-to-end execution of a process lifecycle from admission to termination.

---

## 🎯 Syllabus & Rubric Alignment (100 Marks)

| Phase | Milestone Title | Mark Weight | Deliverable in this Repository |
| :--- | :--- | :---: | :--- |
| **Phase 1** | System Design & Planning | **20 Marks** | Modular architecture, unified `Process`/PCB data structures, I/O flow in `sim/pcb.py` and `reports/PROJECT_REPORT.md`. |
| **Phase 2** | Core Resource Modules | **20 Marks** | 4 fully implemented modules in `sim/` with Bash orchestration scripts (`run.sh`, `system_probe.sh`). |
| **Phase 3** | Analysis & Comparison | **20 Marks** | Automated comparative benchmarking (`benchmark.sh`), ASCII/PNG Gantt charts, Page fault curves, and Disk seek trajectory plots. |
| **Phase 4** | Testing & Reliability | **20 Marks** | Automated test harness (`test_suite.sh`) with 32 unit tests verifying boundary values, zero quantum, negative inputs, and activity logging (`sim_activity.log`). |
| **Phase 5** | Documentation & Demonstration | **20 Marks** | Comprehensive `README.md`, full academic report (`reports/PROJECT_REPORT.md`), and Viva preparation guide. |

---

## 📁 Repository Structure
```text
os-simbench/
├── run.sh                  # Main Ubuntu/WSL2 Bash launcher
├── web.sh                  # Interactive Web Dashboard launcher (WSL2/Linux)
├── benchmark.sh            # Automated batch benchmark suite runner
├── test_suite.sh           # Automated unit and boundary test harness
├── system_probe.sh         # Linux /proc diagnostic telemetry probe
├── run.bat                 # Windows standalone runner
├── web.bat                 # Windows Web Dashboard launcher (opens browser)
├── requirements.txt        # Python dependencies (matplotlib, tabulate)
├── main.py                 # Integrated application CLI & interactive menu
├── web_server.py           # Zero-dependency Python HTTP API server
├── web/                    # Modern responsive Web Dashboard
│   └── index.html          # Interactive SPA (Tailwind + Chart.js)
├── sim/
│   ├── __init__.py
│   ├── pcb.py              # Process Control Block & lifecycle states
│   ├── cpu_scheduler.py    # FCFS, SJF, SRTF, Priority, RR, MLFQ
│   ├── memory_manager.py   # FIFO, LRU, Optimal, Clock, Belady Anomaly, Fragmentation
│   ├── deadlock.py         # Banker's Safety & Request Evaluator, RAG
│   ├── disk_scheduler.py   # FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
│   ├── visualizer.py       # ASCII tables, Gantt charts, Matplotlib plots
│   └── logger.py           # Structured event logging engine
├── data/
│   ├── cpu_workloads.json      # Standard, staggered, and convoy workloads
│   ├── memory_traces.json     # Silberschatz canonical & Belady anomaly traces
│   ├── deadlock_scenarios.json# Safe & unsafe resource matrices
│   └── disk_workloads.json    # Cylinder request queues
├── tests/
│   ├── test_cpu.py         # CPU scheduler unit tests
│   ├── test_memory.py      # Page replacement & Belady tests
│   ├── test_deadlock.py    # Banker's safety & request rejection tests
│   ├── test_disk.py        # Disk seek distance validations
│   └── test_boundary.py    # Exception handling & boundary validations
└── reports/
    ├── PROJECT_REPORT.md   # Comprehensive academic capstone report
    ├── charts/             # High-resolution generated PNG plots
    └── logs/               # Persistent simulation activity logs
```

---

## 🚀 Quickstart & Execution

### 1. Running in Ubuntu 24.04 LTS (WSL2)
Ensure scripts have execution permissions:
```bash
chmod +x run.sh web.sh benchmark.sh test_suite.sh system_probe.sh
```

#### Launch Interactive Web Dashboard:
```bash
./web.sh
# Opens interactive UI at http://localhost:8080
```

#### Launch Interactive CLI Menu:
```bash
./run.sh
```

#### Run Automated Full-Benchmark Suite:
```bash
./benchmark.sh
```

#### Run All Unit & Reliability Tests:
```bash
./test_suite.sh
```

#### Inspect Live Host Kernel Diagnostics:
```bash
./system_probe.sh
```

---

### 2. Running on Windows (Directly)

#### Launch Interactive Web Dashboard:
Double-click `web.bat` or run:
```powershell
python main.py --web
# Automatically accessible at http://localhost:8080
```

#### Launch Interactive CLI Menu:
```powershell
python main.py
```
Or directly trigger batch benchmarks:
```powershell
python main.py --benchmark
python main.py --test
```

---

## 📊 Sample Output Traces

### CPU Comparative Performance (Standard Workload):
```text
+--------------------------------+------------+------+------------+---------+--------+--------+------------+
|           Algorithm            | Total Time | Idle | CPU Util % | Avg TAT | Avg WT | Avg RT | Throughput |
+--------------------------------+------------+------+------------+---------+--------+--------+------------+
| FCFS                           | 26         | 0    | 100.0%     | 13.40   | 8.20   | 8.20   | 0.1923     |
| SJF (Non-Preemptive)           | 26         | 0    | 100.0%     | 11.80   | 6.60   | 6.60   | 0.1923     |
| SRTF (Preemptive SJF)          | 26         | 0    | 100.0%     | 11.60   | 6.40   | 5.80   | 0.1923     |
| Priority (Non-Preemptive)      | 26         | 0    | 100.0%     | 11.80   | 6.60   | 6.60   | 0.1923     |
| Priority (Preemptive)          | 26         | 0    | 100.0%     | 11.60   | 6.40   | 5.80   | 0.1923     |
| Round Robin (q=2)              | 26         | 0    | 100.0%     | 17.80   | 12.60  | 2.80   | 0.1923     |
| MLFQ (Q0:q=2, Q1:q=4, Q2:FCFS) | 26         | 0    | 100.0%     | 17.80   | 12.60  | 2.00   | 0.1923     |
+--------------------------------+------------+------+------------+---------+--------+--------+------------+
```

### Page Replacement Performance (3 Frames):
```text
+-----------------------+--------+------------------+--------+------+--------------+------------+
|       Algorithm       | Frames | Total References | Faults | Hits | Fault Rate % | Hit Rate % |
+-----------------------+--------+------------------+--------+------+--------------+------------+
| FIFO                  | 3      | 20               | 15     | 5    | 75.0%        | 25.0%      |
| LRU                   | 3      | 20               | 12     | 8    | 60.0%        | 40.0%      |
| Optimal               | 3      | 20               | 9      | 11   | 45.0%        | 55.0%      |
| Clock (Second Chance) | 3      | 20               | 14     | 6    | 70.0%        | 30.0%      |
+-----------------------+--------+------------------+--------+------+--------------+------------+
```

---

## 📈 Generated Visual Charts (`reports/charts/`)
- `cpu_comparison.png`: Bar comparison of Waiting Time & Turnaround Time across all 7 CPU schedulers.
- `cpu_best_gantt.png`: Gantt chart breakdown of execution time slices.
- `page_fault_curves.png`: Multi-frame sensitivity analysis curves showing page fault counts from 2 to 6 frames.
- `disk_trajectories.png`: Multi-line trajectory plots illustrating cylinder seek pathing.

---

## 📝 Full Capstone Documentation
See [`reports/PROJECT_REPORT.md`](file:///reports/PROJECT_REPORT.md) for the complete academic report, algorithm formalizations, and Viva Voce preparation section.
