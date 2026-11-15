# Operating Systems Laboratory (ENSC-351) - Capstone Project Report

**Project Title:** OS-SimBench: An Integrated Operating System Resource Management Simulator & Benchmark Suite  
**Course:** B.Tech Semester V, Operating Systems Laboratory (ENSC-351)  
**Submitted By:**
* **Kunal Yadav** (Roll No: `2401730157`)
* **Yashasvi Bhagour** (Roll No: `2401730074`)
* **Vanshika** (Roll No: `2501732297`)

**Environment:** Ubuntu 24.04 LTS (WSL2), Python 3.14.x, Bash Shell, Visual Studio Code, Git  
**Total Marks:** 100 Marks (Phases 1 through 5)  

---

## 1. Executive Summary & Problem Definition

Modern Operating Systems manage complex shared hardware resources—central processors, main memory hierarchies, peripheral storage disks, and non-preemptible device handles—under competing constraints of fairness, latency, throughput, and system stability. In academic curricula, these subsystems are frequently taught in isolation, obscuring how changes in one subsystem (e.g., memory paging delays) cascade into others (e.g., process starvation or disk thrashing).

The objective of **`OS-SimBench`** is to develop a unified, cohesive simulation platform combining **Python 3** and **Bash scripting** to model, benchmark, and visualize the major operational layers of an operating system:
1. **CPU Process Scheduling:** Evaluating preemptive and non-preemptive strategies against CPU utilization and waiting times.
2. **Virtual Memory & Page Replacement:** Modeling paging architectures, frame allocation sensitivity, and anomaly states.
3. **Deadlock Management:** Ensuring safe execution states using Dijkstra's Banker's Algorithm and detecting deadlock cycles.
4. **Secondary Storage Head Scheduling:** Optimizing mechanical disk seek trajectories and track traversal distances.
5. **Integrated Workflow:** Simulating complete process lifecycles across admission, paging, resource acquisition, scheduling, I/O, and termination.

---

## 2. Phase 1: System Design and Planning (20 Marks)

### 2.1 Architectural Overview
`OS-SimBench` employs a layered, modular object-oriented design where data structures are decoupled from scheduling policies, permitting side-by-side benchmarking on identical workloads.

```
                           +---------------------------+
                           |  Bash Orchestration Layer  |
                           |  (run.sh, benchmark.sh)   |
                           +-------------+-------------+
                                         |
                           +-------------v-------------+
                           |    CLI & Menu Controller   |
                           |         (main.py)         |
                           +-------------+-------------+
                                         |
     +-------------------+---------------+-------------------+-------------------+
     |                   |                                   |                   |
+----v-----+       +-----v------+                      +-----v------+      +-----v----+
|   CPU    |       |   Memory   |                      |  Deadlock  |      |   Disk   |
|Scheduler |       |  Manager   |                      |  Manager   |      |Scheduler |
+----+-----+       +-----+------+                      +-----+------+      +-----+----+
     |                   |                                   |                   |
     +-------------------+---------------+-------------------+-------------------+
                                         |
                           +-------------v-------------+
                           | Structured Activity Logs  |
                           |  & Visualizer (PNG/ASCII) |
                           +---------------------------+
```

### 2.2 Core Data Structures (`sim/pcb.py`)
Central to the architecture is the **Process Control Block (PCB)**, instantiated via the `Process` class:

* `pid` (`str`): Unique process identifier (e.g., `"P1"`, `"JOB_101"`).
* `arrival_time` (`int`): Simulation tick at which process enters the `READY` queue ($t \ge 0$).
* `burst_time` (`int`): Required CPU execution ticks ($t > 0$).
* `remaining_time` (`int`): Remaining CPU time units prior to termination.
* `priority` (`int`): Priority ranking (lower integer indicates higher priority).
* `pages` (`List[int]`): Reference string of virtual memory page addresses accessed during execution.
* `allocated_resources` / `max_resources` (`List[int]`): Multi-resource vectors for Banker's evaluation.
* `disk_requests` (`List[int]`): Track cylinder addresses requested for disk I/O.
* `state` (`ProcessState` Enum): `NEW`, `READY`, `RUNNING`, `WAITING`, `TERMINATED`.
* Dynamic Metrics: `start_time`, `completion_time`, `turnaround_time`, `waiting_time`, `response_time`.

### 2.3 Mathematical Metrics Formulations
* **Turnaround Time ($TAT$):**
  $$TAT = CompletionTime - ArrivalTime$$
* **Waiting Time ($WT$):**
  $$WT = TurnaroundTime - BurstTime$$
* **Response Time ($RT$):**
  $$RT = FirstExecutionStartTime - ArrivalTime$$
* **CPU Utilization ($U$):**
  $$U = \left( \frac{\text{Total Busy Ticks}}{\text{Total Simulation Ticks}} \right) \times 100\%$$
* **Total Head Movement ($THM$):**
  $$THM = \sum_{i=1}^{k} |Track_i - Track_{i-1}|$$

---

## 3. Phase 2: Core Resource-Management Modules (20 Marks)

### 3.1 Module 1: CPU Scheduling (`sim/cpu_scheduler.py`)
Implemented algorithms:
1. **First-Come, First-Served (FCFS):** Non-preemptive, services processes in order of arrival.
2. **Shortest Job First (SJF - Non-Preemptive):** Prioritizes processes with shortest total burst times.
3. **Shortest Remaining Time First (SRTF):** Preemptive SJF; context-switches immediately when an arriving job has shorter remaining time than currently running job.
4. **Priority Scheduling (Non-Preemptive & Preemptive):** Dispatches highest-priority processes.
5. **Round Robin (RR):** Preemptive time-sharing scheduler using a circular FIFO queue and configurable time quantum $q$.
6. **Multilevel Feedback Queue (MLFQ):** 3-level queue architecture:
   * Level 0 ($Q_0$): Round Robin with quantum $q=2$.
   * Level 1 ($Q_1$): Round Robin with quantum $q=4$.
   * Level 2 ($Q_2$): FCFS for compute-bound background jobs.
   * **Starvation Prevention:** Periodic priority promotion (Aging interval $T_{age}=20$ ticks).

### 3.2 Module 2: Memory Management (`sim/memory_manager.py`)
* **Page Replacement Policies:**
  * **FIFO:** Evicts page in memory the longest via a FIFO queue.
  * **LRU:** Evicts page whose last access timestamp is lowest.
  * **Optimal (Belady's Min):** Evicts page that will not be referenced for the furthest duration in the future (theoretical lower bound).
  * **Clock (Second Chance):** Maintains circular frame buffer with reference bits; skips pages with $R=1$ while clearing them, evicting first page encountered with $R=0$.
* **Belady's Anomaly Detection:** Verifies anomaly scenarios where increasing frame allocations produces more page faults under FIFO.
* **Contiguous Allocation:** First-Fit, Best-Fit, and Worst-Fit algorithms tracking internal and external fragmentation.

### 3.3 Module 3: Deadlock Avoidance (`sim/deadlock.py`)
* **Banker's Safety Algorithm:** Iteratively tests whether there exists a safe sequence where remaining resource needs can be met by current available vectors plus released allocations:
  $$Need[i][j] \le Work[j] \implies Work[j] = Work[j] + Allocation[i][j]$$
* **Resource-Request Evaluation:** Implements speculative trial allocation:
  1. Validates $Request \le Need_i$ (ensures claim integrity).
  2. Validates $Request \le Available$ (ensures physical availability).
  3. Applies tentative allocation and executes safety verification.
  4. Automatically rolls back state if tentative allocation results in an unsafe state.
* **Wait-For Graph (Cycle Detection):** DFS-based cycle detector identifying deadlocked processes in systems with single resource instances.

### 3.4 Module 4: Disk Storage Scheduling (`sim/disk_scheduler.py`)
* **FCFS:** Traverses requests in arrival order.
* **SSTF:** Greedily moves to the nearest pending track request.
* **SCAN (Elevator):** Moves in one direction servicing tracks until boundary (e.g., track 199), then reverses.
* **C-SCAN:** Moves towards boundary, then wraps around to opposite boundary (track 0) without servicing on return stroke.
* **LOOK & C-LOOK:** Enhanced variants of SCAN/C-SCAN that reverse or wrap at the furthest pending request rather than traveling to extreme physical disk bounds.

### 3.5 Bash Script Integration
* `run.sh`: Automated launcher that validates Python 3 and runs the interactive menu.
* `benchmark.sh`: Executes batch benchmarks unattended and dumps comparative metrics.
* `system_probe.sh`: Inspects live Linux kernel metrics via `/proc/cpuinfo`, `/proc/meminfo`, and `/proc/stat`.

---

## 4. Phase 3: Analysis and Comparison (20 Marks)

### 4.1 CPU Scheduling Benchmark (Workload: 5 Balanced Processes)
Input dataset:
* $P_1$: Arrival=0, Burst=5, Priority=2
* $P_2$: Arrival=1, Burst=3, Priority=1
* $P_3$: Arrival=2, Burst=8, Priority=4
* $P_4$: Arrival=3, Burst=6, Priority=3
* $P_5$: Arrival=4, Burst=4, Priority=2

#### Experimental Results:
| Algorithm | Total Time | Idle Time | CPU Util % | Avg TAT (Ticks) | Avg WT (Ticks) | Avg RT (Ticks) | Throughput (procs/tick) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FCFS** | 26 | 0 | 100.0% | 13.40 | 8.20 | 8.20 | 0.1923 |
| **SJF (Non-Preemptive)** | 26 | 0 | 100.0% | 11.80 | 6.60 | 6.60 | 0.1923 |
| **SRTF (Preemptive SJF)** | 26 | 0 | 100.0% | **11.60** | **6.40** | 5.80 | 0.1923 |
| **Priority (Non-Preemptive)**| 26 | 0 | 100.0% | 11.80 | 6.60 | 6.60 | 0.1923 |
| **Priority (Preemptive)** | 26 | 0 | 100.0% | **11.60** | **6.40** | 5.80 | 0.1923 |
| **Round Robin ($q=2$)** | 26 | 0 | 100.0% | 17.80 | 12.60 | **2.80** | 0.1923 |
| **MLFQ** | 26 | 0 | 100.0% | 17.80 | 12.60 | **2.00** | 0.1923 |

**Key Findings:**
1. **Minimizing Latency vs. Responsiveness:** SRTF achieved the lowest Average Waiting Time (6.40 ticks) and Average Turnaround Time (11.60 ticks). However, Round Robin and MLFQ demonstrated superior Response Time (2.80 and 2.00 ticks), making them significantly better suited for interactive user workloads.
2. **Convoy Effect:** FCFS suffered from queue head blocking where shorter jobs ($P_2, P_5$) waited behind compute jobs.

### 4.2 Page Replacement Benchmark (Workload: Silberschatz 20-Page Trace, 3 Frames)
Reference sequence: `[7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]`

| Algorithm | Frames | Page Faults | Page Hits | Fault Rate (%) | Hit Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FIFO** | 3 | 15 | 5 | 75.0% | 25.0% |
| **Clock (Second Chance)** | 3 | 14 | 6 | 70.0% | 30.0% |
| **LRU** | 3 | 12 | 8 | 60.0% | 40.0% |
| **Optimal (MIN)** | 3 | **9** | **11** | **45.0%** | **55.0%** |

**Key Findings:**
1. **Optimal Boundary:** The Optimal algorithm established the absolute theoretical performance boundary (9 faults, 55% hit rate).
2. **LRU Approximation:** Clock achieved near-LRU performance (14 vs. 12 faults) with low hardware overhead ($O(1)$ reference bit scan rather than timestamp updates).
3. **Belady's Anomaly:** Tested with canonical trace `[1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]`:
   * 3 Frames = 9 Faults.
   * 4 Frames = 10 Faults.
   * Confirms that FIFO is not a stack algorithm and does not satisfy the inclusion property.

### 4.3 Disk Scheduling Benchmark (Workload: 8 Requests, Initial Head: 53)
Request sequence: `[98, 183, 37, 122, 14, 124, 65, 67]`

| Algorithm | Total Head Movement (Cylinders) | Avg Seek Distance | Direction / Bounds |
| :--- | :---: | :---: | :--- |
| **FCFS** | 640 | 80.00 | Unordered |
| **C-SCAN** | 382 | 38.20 | Direction: High, Touches 199 and 0 |
| **SCAN** | 331 | 36.78 | Direction: High, Touches 199 |
| **C-LOOK** | 322 | 40.25 | Direction: High, Wraps at 14 |
| **LOOK** | 299 | 37.38 | Direction: High, Reverses at 183 |
| **SSTF** | **236** | **29.50** | Nearest neighbor greedy |

**Key Findings:**
* SSTF reduced head movement by **63.1%** compared to FCFS (236 vs. 640 cylinders).
* LOOK out-performed SCAN (299 vs. 331 cylinders) by eliminating unnecessary head travel to cylinder 199.

---

## 5. Phase 4: Testing and Reliability (20 Marks)

### 5.1 Test Suite Structure
A rigorous suite of **32 unit tests** was implemented across 5 test modules using Python's standard `unittest` framework:
* `tests/test_cpu.py`: 5 test cases checking schedule correctness, Gantt compression, and metrics.
* `tests/test_memory.py`: 6 test cases verifying textbook fault counts, Clock rotation, and Belady anomaly detection.
* `tests/test_deadlock.py`: 5 test cases validating safe sequence generation, safe request granting, claim exceedance rejection, and automatic unsafe rollback.
* `tests/test_disk.py`: 5 test cases validating seek distance calculations against textbook benchmarks.
* `tests/test_boundary.py`: 11 test cases verifying exception handling for invalid/boundary inputs.

### 5.2 Boundary & Invalid Input Verification Matrix
| Test Case Identifier | Tested Condition | Injected Input | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- | :---: |
| `TC-BND-01` | Negative Burst Time | `Process(burst_time=-5)` | Raises `ValueError` | **PASSED** |
| `TC-BND-02` | Zero Burst Time | `Process(burst_time=0)` | Raises `ValueError` | **PASSED** |
| `TC-BND-03` | Negative Arrival Time | `Process(arrival_time=-2)` | Raises `ValueError` | **PASSED** |
| `TC-BND-04` | Zero Round Robin Quantum | `schedule_round_robin(q=0)` | Raises `ValueError` | **PASSED** |
| `TC-BND-05` | Empty Process Queue | `schedule_fcfs([])` | Raises `ValueError` | **PASSED** |
| `TC-BND-06` | Zero Memory Frames | `fifo(frames=0)` | Raises `ValueError` | **PASSED** |
| `TC-BND-07` | Empty Reference String | `lru([])` | Raises `ValueError` | **PASSED** |
| `TC-BND-08` | Disk Cylinder Out of Bounds | `[50, 250]` on 199-cyl disk | Raises `ValueError` | **PASSED** |
| `TC-BND-09` | Negative Head Position | `initial_head = -1` | Raises `ValueError` | **PASSED** |
| `TC-BND-10` | Mismatched Banker's Dimension | $N=2$ procs, $N=1$ row | Raises `ValueError` | **PASSED** |
| `TC-BND-11` | Allocation Exceeding Max Claim | $Alloc=3 > Max=2$ | Raises `ValueError` | **PASSED** |

### 5.3 Activity Logging Engine (`reports/logs/sim_activity.log`)
All process dispatches, preemption events, frame replacements, Banker's resource requests, and rollback occurrences are timestamped and written to disk:
```text
[2026-11-15 16:16:32] [INFO   ] [Banker's] Safe State confirmed: <P1 -> P3 -> P0 -> P2 -> P4>
[2026-11-15 16:16:32] [WARNING] [Banker's Request] Error: Process 'P1' exceeded its maximum claim on resource R0 (Requested: 2, Need: 1).
[2026-11-15 16:16:32] [WARNING] [Banker's] Unsafe State detected! Blocked: ['P0', 'P1', 'P2', 'P3', 'P4']
[2026-11-15 16:16:32] [WARNING] [Banker's Request] Denied: Granting request to Process 'P0' would transition system into an UNSAFE / DEADLOCK state. Request was rolled back.
```

---

## 6. Phase 5: Demonstration & Viva Voce Preparation (20 Marks)

### Common Viva Voce Examination Questions & Technical Answers

#### Q1: What is the convoy effect in CPU scheduling, and which algorithm eliminates it?
**Answer:** The convoy effect occurs in non-preemptive FCFS when a long CPU-bound process holds the processor, forcing a queue of short I/O-bound processes to wait. This degrades CPU and device utilization. It is eliminated by preemptive algorithms like Round Robin or SRTF, which allocate fixed time slices or prioritize shorter jobs.

#### Q2: Why does Round Robin have higher average turnaround time than SRTF, but remains preferable in modern operating systems?
**Answer:** SRTF is mathematically provable to minimize average turnaround time. However, it requires future knowledge of burst times (unrealistic in general-purpose OSs) and causes starvation for long jobs. Round Robin provides fair time-sharing and minimizes **response time**, ensuring responsive interactive desktop applications.

#### Q3: What is Belady's Anomaly, and why does it occur in FIFO but never in LRU or Optimal?
**Answer:** Belady's Anomaly is the phenomenon where allocating more physical memory frames to a process leads to an increase in page faults. It occurs in FIFO because FIFO does not satisfy the **inclusion property** (the set of pages in $n$ frames is not necessarily a subset of the pages in $n+1$ frames). LRU and Optimal belong to the class of **stack algorithms**, where inclusion is mathematically guaranteed, making Belady's Anomaly impossible.

#### Q4: How does the Clock (Second Chance) algorithm balance the performance of LRU with the simplicity of FIFO?
**Answer:** True LRU requires maintaining either a sorted double-linked list or updating 64-bit hardware timestamps on every memory access ($O(1)$ hardware modification per access, high overhead). The Clock algorithm uses a simple single reference bit ($R$) per frame and a circular pointer. On page access, hardware sets $R=1$. On page fault, the clock hand advances: if $R=1$, it gives a second chance ($R=0$); if $R=0$, the page is evicted.

#### Q5: Is an unsafe state in Banker's algorithm synonymous with a deadlocked state?
**Answer:** No. An unsafe state is not necessarily a deadlocked state, but a state from which the system cannot guarantee that a deadlock will not occur. If processes request their maximum declared resources, an unsafe state will inevitably degenerate into a deadlock. Conversely, every deadlocked state is an unsafe state.

#### Q6: Why is LOOK scheduling generally preferred over SCAN?
**Answer:** SCAN always travels to the extreme physical boundary cylinder (e.g., track 199 or 0) before reversing, regardless of whether requests exist at that boundary. LOOK inspects the request queue and reverses direction immediately after servicing the furthest pending request, eliminating unnecessary mechanical head travel.

---

## 7. Conclusion
The **`OS-SimBench`** capstone successfully implements an integrated, modular simulation platform combining Python 3 and Bash in Ubuntu 24.04 (WSL2). By providing automated comparative benchmarks, mathematical performance metrics, visual trajectory and Gantt plots, rigorous unit and boundary tests, and full execution traces, the project satisfies all rubric requirements for the ENSC-351 Operating Systems Laboratory Capstone.
