"""
Module: cpu_scheduler.py
Implements core CPU scheduling algorithms for OS-SimBench:
- FCFS (First-Come, First-Served)
- SJF (Shortest Job First - Non-Preemptive)
- SRTF (Shortest Remaining Time First - Preemptive SJF)
- Priority (Non-Preemptive & Preemptive)
- Round Robin (RR - Configurable Quantum)
- Multilevel Feedback Queue (MLFQ - 3 Priority Queues with Aging)
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from collections import deque
from sim.pcb import Process, ProcessState
from sim.logger import get_sim_logger

@dataclass
class CPUScheduleResult:
    algorithm_name: str
    gantt_chart: List[Tuple[int, int, str]]  # [(start_time, end_time, pid)]
    processes: List[Process]
    total_time: int
    idle_time: int
    cpu_utilization: float
    avg_turnaround_time: float
    avg_waiting_time: float
    avg_response_time: float
    throughput: float

    def get_summary_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm_name,
            "total_time": self.total_time,
            "idle_time": self.idle_time,
            "cpu_utilization": round(self.cpu_utilization, 2),
            "avg_tat": round(self.avg_turnaround_time, 2),
            "avg_wt": round(self.avg_waiting_time, 2),
            "avg_rt": round(self.avg_response_time, 2),
            "throughput": round(self.throughput, 4)
        }

class CPUScheduler:
    def __init__(self):
        self.logger = get_sim_logger()

    def _prepare_processes(self, processes: List[Process]) -> List[Process]:
        if not processes:
            raise ValueError("Process list cannot be empty.")
        cloned = [p.clone() for p in processes]
        for p in cloned:
            p.reset()
        return cloned

    def _compress_gantt(self, raw_gantt: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
        """Merges contiguous timeline slices for the same PID."""
        if not raw_gantt:
            return []
        compressed = []
        cur_start, cur_end, cur_pid = raw_gantt[0]
        for start, end, pid in raw_gantt[1:]:
            if pid == cur_pid and start == cur_end:
                cur_end = end
            else:
                compressed.append((cur_start, cur_end, cur_pid))
                cur_start, cur_end, cur_pid = start, end, pid
        compressed.append((cur_start, cur_end, cur_pid))
        return compressed

    def _calculate_metrics(self, name: str, processes: List[Process], gantt: List[Tuple[int, int, str]], total_time: int) -> CPUScheduleResult:
        n = len(processes)
        for p in processes:
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            if p.response_time < 0:
                p.response_time = p.waiting_time
            p.state = ProcessState.TERMINATED

        idle_time = sum(end - start for start, end, pid in gantt if pid == "IDLE")
        busy_time = total_time - idle_time
        cpu_util = (busy_time / total_time * 100.0) if total_time > 0 else 0.0
        avg_tat = sum(p.turnaround_time for p in processes) / n
        avg_wt = sum(p.waiting_time for p in processes) / n
        avg_rt = sum(p.response_time for p in processes) / n
        throughput = n / total_time if total_time > 0 else 0.0

        compressed_gantt = self._compress_gantt(gantt)
        self.logger.info(f"[{name}] Finished. Total Time: {total_time}, Avg WT: {avg_wt:.2f}, Avg TAT: {avg_tat:.2f}, CPU Util: {cpu_util:.1f}%")

        return CPUScheduleResult(
            algorithm_name=name,
            gantt_chart=compressed_gantt,
            processes=processes,
            total_time=total_time,
            idle_time=idle_time,
            cpu_utilization=cpu_util,
            avg_turnaround_time=avg_tat,
            avg_waiting_time=avg_wt,
            avg_response_time=avg_rt,
            throughput=throughput
        )

    # -------------------------------------------------------------
    # 1. First-Come, First-Served (FCFS)
    # -------------------------------------------------------------
    def schedule_fcfs(self, processes: List[Process]) -> CPUScheduleResult:
        procs = sorted(self._prepare_processes(processes), key=lambda x: (x.arrival_time, x.pid))
        current_time = 0
        gantt = []

        for p in procs:
            if current_time < p.arrival_time:
                gantt.append((current_time, p.arrival_time, "IDLE"))
                current_time = p.arrival_time

            p.start_time = current_time
            p.response_time = current_time - p.arrival_time
            start = current_time
            current_time += p.burst_time
            p.completion_time = current_time
            p.remaining_time = 0
            gantt.append((start, current_time, p.pid))

        return self._calculate_metrics("FCFS", procs, gantt, current_time)

    # -------------------------------------------------------------
    # 2. Shortest Job First (SJF - Non-Preemptive)
    # -------------------------------------------------------------
    def schedule_sjf(self, processes: List[Process]) -> CPUScheduleResult:
        procs = self._prepare_processes(processes)
        completed = []
        current_time = 0
        gantt = []
        ready_pool = list(procs)

        while len(completed) < len(procs):
            available = [p for p in ready_pool if p.arrival_time <= current_time]
            if not available:
                next_arrival = min(p.arrival_time for p in ready_pool)
                gantt.append((current_time, next_arrival, "IDLE"))
                current_time = next_arrival
                continue

            chosen = min(available, key=lambda x: (x.burst_time, x.arrival_time, x.pid))
            ready_pool.remove(chosen)

            chosen.start_time = current_time
            chosen.response_time = current_time - chosen.arrival_time
            start = current_time
            current_time += chosen.burst_time
            chosen.completion_time = current_time
            chosen.remaining_time = 0
            gantt.append((start, current_time, chosen.pid))
            completed.append(chosen)

        return self._calculate_metrics("SJF (Non-Preemptive)", completed, gantt, current_time)

    # -------------------------------------------------------------
    # 3. Shortest Remaining Time First (SRTF - Preemptive)
    # -------------------------------------------------------------
    def schedule_srtf(self, processes: List[Process]) -> CPUScheduleResult:
        procs = self._prepare_processes(processes)
        n = len(procs)
        completed_count = 0
        current_time = 0
        gantt = []

        while completed_count < n:
            available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]
            if not available:
                unstarted = [p for p in procs if p.remaining_time > 0]
                next_arrival = min(p.arrival_time for p in unstarted)
                gantt.append((current_time, next_arrival, "IDLE"))
                current_time = next_arrival
                continue

            chosen = min(available, key=lambda x: (x.remaining_time, x.arrival_time, x.pid))
            if chosen.start_time == -1:
                chosen.start_time = current_time
                chosen.response_time = current_time - chosen.arrival_time

            gantt.append((current_time, current_time + 1, chosen.pid))
            chosen.remaining_time -= 1
            current_time += 1

            if chosen.remaining_time == 0:
                chosen.completion_time = current_time
                completed_count += 1

        return self._calculate_metrics("SRTF (Preemptive SJF)", procs, gantt, current_time)

    # -------------------------------------------------------------
    # 4. Priority Scheduling (Non-Preemptive, Lower integer = Higher priority)
    # -------------------------------------------------------------
    def schedule_priority(self, processes: List[Process]) -> CPUScheduleResult:
        procs = self._prepare_processes(processes)
        completed = []
        current_time = 0
        gantt = []
        ready_pool = list(procs)

        while len(completed) < len(procs):
            available = [p for p in ready_pool if p.arrival_time <= current_time]
            if not available:
                next_arrival = min(p.arrival_time for p in ready_pool)
                gantt.append((current_time, next_arrival, "IDLE"))
                current_time = next_arrival
                continue

            chosen = min(available, key=lambda x: (x.priority, x.arrival_time, x.pid))
            ready_pool.remove(chosen)

            chosen.start_time = current_time
            chosen.response_time = current_time - chosen.arrival_time
            start = current_time
            current_time += chosen.burst_time
            chosen.completion_time = current_time
            chosen.remaining_time = 0
            gantt.append((start, current_time, chosen.pid))
            completed.append(chosen)

        return self._calculate_metrics("Priority (Non-Preemptive)", completed, gantt, current_time)

    # -------------------------------------------------------------
    # 5. Priority Scheduling (Preemptive)
    # -------------------------------------------------------------
    def schedule_priority_preemptive(self, processes: List[Process]) -> CPUScheduleResult:
        procs = self._prepare_processes(processes)
        n = len(procs)
        completed_count = 0
        current_time = 0
        gantt = []

        while completed_count < n:
            available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]
            if not available:
                unstarted = [p for p in procs if p.remaining_time > 0]
                next_arrival = min(p.arrival_time for p in unstarted)
                gantt.append((current_time, next_arrival, "IDLE"))
                current_time = next_arrival
                continue

            chosen = min(available, key=lambda x: (x.priority, x.arrival_time, x.pid))
            if chosen.start_time == -1:
                chosen.start_time = current_time
                chosen.response_time = current_time - chosen.arrival_time

            gantt.append((current_time, current_time + 1, chosen.pid))
            chosen.remaining_time -= 1
            current_time += 1

            if chosen.remaining_time == 0:
                chosen.completion_time = current_time
                completed_count += 1

        return self._calculate_metrics("Priority (Preemptive)", procs, gantt, current_time)

    # -------------------------------------------------------------
    # 6. Round Robin (RR - Configurable Quantum)
    # -------------------------------------------------------------
    def schedule_round_robin(self, processes: List[Process], quantum: int = 2) -> CPUScheduleResult:
        if quantum <= 0:
            raise ValueError(f"Time quantum must be strictly positive (got {quantum}).")

        procs = self._prepare_processes(processes)
        procs_sorted = sorted(procs, key=lambda x: (x.arrival_time, x.pid))
        queue = deque()
        current_time = 0
        gantt = []
        arrived_idx = 0
        n = len(procs)
        completed_count = 0

        # Enqueue initial arrivals at current_time=0
        while arrived_idx < n and procs_sorted[arrived_idx].arrival_time <= current_time:
            queue.append(procs_sorted[arrived_idx])
            arrived_idx += 1

        while completed_count < n:
            if not queue:
                if arrived_idx < n:
                    next_arrival = procs_sorted[arrived_idx].arrival_time
                    gantt.append((current_time, next_arrival, "IDLE"))
                    current_time = next_arrival
                    while arrived_idx < n and procs_sorted[arrived_idx].arrival_time <= current_time:
                        queue.append(procs_sorted[arrived_idx])
                        arrived_idx += 1
                continue

            current_proc = queue.popleft()
            if current_proc.start_time == -1:
                current_proc.start_time = current_time
                current_proc.response_time = current_time - current_proc.arrival_time

            exec_time = min(quantum, current_proc.remaining_time)
            gantt.append((current_time, current_time + exec_time, current_proc.pid))
            current_proc.remaining_time -= exec_time
            current_time += exec_time

            # Enqueue any new processes arriving during execution
            while arrived_idx < n and procs_sorted[arrived_idx].arrival_time <= current_time:
                queue.append(procs_sorted[arrived_idx])
                arrived_idx += 1

            if current_proc.remaining_time > 0:
                queue.append(current_proc)
            else:
                current_proc.completion_time = current_time
                completed_count += 1

        return self._calculate_metrics(f"Round Robin (q={quantum})", procs_sorted, gantt, current_time)

    # -------------------------------------------------------------
    # 7. Multilevel Feedback Queue (MLFQ)
    # Queue 0: RR (q=2) -> Queue 1: RR (q=4) -> Queue 2: FCFS
    # Periodic Aging prevents starvation
    # -------------------------------------------------------------
    def schedule_mlfq(self, processes: List[Process], q0_quantum: int = 2, q1_quantum: int = 4, aging_interval: int = 20) -> CPUScheduleResult:
        procs = self._prepare_processes(processes)
        procs_sorted = sorted(procs, key=lambda x: (x.arrival_time, x.pid))
        
        q0 = deque()
        q1 = deque()
        q2 = deque()
        
        current_time = 0
        gantt = []
        arrived_idx = 0
        n = len(procs)
        completed_count = 0
        last_aging_time = 0

        def check_arrivals():
            nonlocal arrived_idx, current_time
            while arrived_idx < n and procs_sorted[arrived_idx].arrival_time <= current_time:
                p = procs_sorted[arrived_idx]
                p.queue_level = 0
                q0.append(p)
                arrived_idx += 1

        def check_aging():
            nonlocal last_aging_time, current_time
            if aging_interval > 0 and (current_time - last_aging_time) >= aging_interval:
                # Promote processes from Q2 -> Q1 and Q1 -> Q0
                while q2:
                    p = q2.popleft()
                    p.queue_level = 1
                    q1.append(p)
                while q1:
                    p = q1.popleft()
                    p.queue_level = 0
                    q0.append(p)
                last_aging_time = current_time
                self.logger.debug(f"Aging triggered at t={current_time}: promoted all waiting processes.")

        check_arrivals()

        while completed_count < n:
            check_aging()
            check_arrivals()

            if not q0 and not q1 and not q2:
                if arrived_idx < n:
                    next_arrival = procs_sorted[arrived_idx].arrival_time
                    gantt.append((current_time, next_arrival, "IDLE"))
                    current_time = next_arrival
                    check_arrivals()
                continue

            if q0:
                p = q0.popleft()
                time_slice = q0_quantum
                next_level = 1
            elif q1:
                p = q1.popleft()
                time_slice = q1_quantum
                next_level = 2
            else:
                p = q2.popleft()
                time_slice = p.remaining_time  # FCFS run to completion unless preempted by new arrival
                next_level = 2

            if p.start_time == -1:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            # In Q2 (FCFS), a new arrival in higher queue might preempt
            exec_time = min(time_slice, p.remaining_time)
            # Check if an earlier arrival preempts
            gantt.append((current_time, current_time + exec_time, p.pid))
            p.remaining_time -= exec_time
            current_time += exec_time

            check_arrivals()

            if p.remaining_time > 0:
                p.queue_level = next_level
                if next_level == 1:
                    q1.append(p)
                else:
                    q2.append(p)
            else:
                p.completion_time = current_time
                completed_count += 1

        return self._calculate_metrics("MLFQ (Q0:q=2, Q1:q=4, Q2:FCFS)", procs_sorted, gantt, current_time)
