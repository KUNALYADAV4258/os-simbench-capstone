"""
Module: deadlock.py
Implements Deadlock Avoidance and Detection algorithms for OS-SimBench:
1. Banker's Algorithm (Dijkstra):
   - Safety Algorithm (with step-by-step trace)
   - Resource-Request Algorithm (with atomic rollback on unsafe states)
2. Resource Allocation Graph (RAG) / Wait-For Graph Cycle Detector
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
import copy
from sim.logger import get_sim_logger

@dataclass
class SafetyResult:
    is_safe: bool
    safe_sequence: List[str]
    trace: List[str]
    work_history: List[List[int]]

@dataclass
class RequestResult:
    granted: bool
    reason: str
    is_safe: bool
    safe_sequence: List[str]
    system_state: Dict[str, Any]

class DeadlockManager:
    def __init__(self, process_ids: List[str], available: List[int], max_matrix: List[List[int]], allocation_matrix: List[List[int]]):
        self.logger = get_sim_logger()
        self.process_ids = list(process_ids)
        self.available = list(available)
        self.max_matrix = [list(row) for row in max_matrix]
        self.allocation = [list(row) for row in allocation_matrix]
        self._validate_and_compute_need()

    def _validate_and_compute_need(self):
        n = len(self.process_ids)
        m = len(self.available)

        if len(self.max_matrix) != n or len(self.allocation) != n:
            raise ValueError(f"Matrix process rows must match process_ids count ({n}).")

        self.need = []
        for i in range(n):
            if len(self.max_matrix[i]) != m or len(self.allocation[i]) != m:
                raise ValueError(f"Process {self.process_ids[i]} resource vector length must match available resource count ({m}).")

            need_row = []
            for j in range(m):
                if self.allocation[i][j] < 0 or self.max_matrix[i][j] < 0:
                    raise ValueError(f"Resource values cannot be negative at P{self.process_ids[i]}, R{j}.")
                if self.allocation[i][j] > self.max_matrix[i][j]:
                    raise ValueError(f"Allocation cannot exceed Max for Process {self.process_ids[i]} on Resource R{j} ({self.allocation[i][j]} > {self.max_matrix[i][j]}).")
                need_row.append(self.max_matrix[i][j] - self.allocation[i][j])
            self.need.append(need_row)

    def get_state_dict(self) -> Dict[str, Any]:
        return {
            "processes": self.process_ids,
            "available": list(self.available),
            "max": [list(r) for r in self.max_matrix],
            "allocation": [list(r) for r in self.allocation],
            "need": [list(r) for r in self.need]
        }

    # -------------------------------------------------------------
    # Safety Algorithm
    # -------------------------------------------------------------
    def check_safety(self) -> SafetyResult:
        n = len(self.process_ids)
        m = len(self.available)
        work = list(self.available)
        finish = [False] * n
        safe_seq = []
        trace = []
        work_history = [list(work)]

        trace.append(f"Initial Work Vector (Available): {work}")

        found_candidate = True
        while found_candidate:
            found_candidate = False
            for i in range(n):
                if not finish[i]:
                    # Check if Need[i] <= Work
                    can_allocate = all(self.need[i][j] <= work[j] for j in range(m))
                    if can_allocate:
                        for j in range(m):
                            work[j] += self.allocation[i][j]
                        finish[i] = True
                        safe_seq.append(self.process_ids[i])
                        found_candidate = True
                        work_history.append(list(work))
                        trace.append(
                            f"Step {len(safe_seq)}: Process '{self.process_ids[i]}' satisfied "
                            f"(Need={self.need[i]} <= Work). Releases Allocation={self.allocation[i]}. New Work={work}."
                        )
                        break

        if all(finish):
            trace.append(f"SUCCESS: System is in a SAFE STATE. Safe Sequence: <{' -> '.join(safe_seq)}>")
            self.logger.info(f"[Banker's] Safe State confirmed: <{' -> '.join(safe_seq)}>")
            return SafetyResult(True, safe_seq, trace, work_history)
        else:
            deadlocked = [self.process_ids[i] for i in range(n) if not finish[i]]
            trace.append(f"FAILURE: System is in an UNSAFE / DEADLOCK STATE. Blocked processes: {deadlocked}")
            self.logger.warning(f"[Banker's] Unsafe State detected! Blocked: {deadlocked}")
            return SafetyResult(False, [], trace, work_history)

    # -------------------------------------------------------------
    # Resource-Request Algorithm
    # -------------------------------------------------------------
    def request_resources(self, pid: str, request: List[int]) -> RequestResult:
        if pid not in self.process_ids:
            raise ValueError(f"Process '{pid}' not recognized in system.")

        p_idx = self.process_ids.index(pid)
        m = len(self.available)

        if len(request) != m:
            raise ValueError(f"Request vector length ({len(request)}) does not match resource types count ({m}).")

        # 1. Check Request <= Need
        for j in range(m):
            if request[j] > self.need[p_idx][j]:
                reason = f"Error: Process '{pid}' exceeded its maximum claim on resource R{j} (Requested: {request[j]}, Need: {self.need[p_idx][j]})."
                self.logger.warning(f"[Banker's Request] {reason}")
                return RequestResult(False, reason, False, [], self.get_state_dict())

        # 2. Check Request <= Available
        for j in range(m):
            if request[j] > self.available[j]:
                reason = f"Wait: Insufficient resources available for Process '{pid}' on resource R{j} (Requested: {request[j]}, Available: {self.available[j]}). Process must wait."
                self.logger.info(f"[Banker's Request] {reason}")
                return RequestResult(False, reason, False, [], self.get_state_dict())

        # 3. Speculative / Trial Allocation
        orig_available = list(self.available)
        orig_allocation = [list(r) for r in self.allocation]
        orig_need = [list(r) for r in self.need]

        for j in range(m):
            self.available[j] -= request[j]
            self.allocation[p_idx][j] += request[j]
            self.need[p_idx][j] -= request[j]

        # 4. Check Safety of tentative state
        safety_res = self.check_safety()

        if safety_res.is_safe:
            reason = f"Success: Request granted to Process '{pid}'. System remains in a safe state with sequence <{' -> '.join(safety_res.safe_sequence)}>."
            self.logger.info(f"[Banker's Request] {reason}")
            return RequestResult(True, reason, True, safety_res.safe_sequence, self.get_state_dict())
        else:
            # Rollback to original state
            self.available = orig_available
            self.allocation = orig_allocation
            self.need = orig_need
            reason = f"Denied: Granting request to Process '{pid}' would transition system into an UNSAFE / DEADLOCK state. Request was rolled back."
            self.logger.warning(f"[Banker's Request] {reason}")
            return RequestResult(False, reason, False, [], self.get_state_dict())

    # -------------------------------------------------------------
    # Wait-For Graph (Cycle Detection for Deadlock Detection)
    # -------------------------------------------------------------
    @staticmethod
    def detect_wait_for_cycles(adjacency_list: Dict[str, List[str]]) -> Tuple[bool, List[List[str]]]:
        """Detects cycles in a Wait-For Graph using Depth First Search."""
        visited = set()
        rec_stack = set()
        cycles = []
        path = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adjacency_list.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle found
                    cycle_start = path.index(neighbor)
                    cycles.append(list(path[cycle_start:] + [neighbor]))

            rec_stack.remove(node)
            path.pop()

        for node in adjacency_list:
            if node not in visited:
                dfs(node)

        return (len(cycles) > 0, cycles)
