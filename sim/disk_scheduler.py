"""
Module: disk_scheduler.py
Implements Secondary Storage / Disk Head Scheduling algorithms for OS-SimBench:
- FCFS (First-Come, First-Served)
- SSTF (Shortest Seek Time First)
- SCAN (Elevator Algorithm)
- C-SCAN (Circular SCAN)
- LOOK
- C-LOOK
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from sim.logger import get_sim_logger

@dataclass
class DiskScheduleResult:
    algorithm_name: str
    initial_head: int
    seek_sequence: List[int]      # [initial_head, req1, req2, ...]
    individual_seeks: List[int]   # [abs(req1 - initial_head), ...]
    total_head_movement: int
    avg_seek_distance: float

    def get_summary_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm_name,
            "initial_head": self.initial_head,
            "requests_count": len(self.seek_sequence) - 1,
            "total_head_movement": self.total_head_movement,
            "avg_seek_distance": round(self.avg_seek_distance, 2),
            "sequence_path": " -> ".join(map(str, self.seek_sequence))
        }

class DiskScheduler:
    def __init__(self, max_cylinder: int = 199):
        self.logger = get_sim_logger()
        self.max_cylinder = max_cylinder

    def _validate_inputs(self, requests: List[int], initial_head: int):
        if not requests:
            raise ValueError("Disk request queue cannot be empty.")
        if initial_head < 0 or initial_head > self.max_cylinder:
            raise ValueError(f"Initial head position {initial_head} out of disk bounds [0, {self.max_cylinder}].")
        for r in requests:
            if r < 0 or r > self.max_cylinder:
                raise ValueError(f"Disk cylinder request {r} out of bounds [0, {self.max_cylinder}].")

    def _build_result(self, name: str, initial_head: int, sequence: List[int]) -> DiskScheduleResult:
        full_seq = [initial_head] + sequence
        seeks = [abs(full_seq[i] - full_seq[i - 1]) for i in range(1, len(full_seq))]
        thm = sum(seeks)
        avg_seek = (thm / len(sequence)) if sequence else 0.0

        self.logger.info(f"[{name}] Total Head Movement: {thm} cylinders, Avg Seek: {avg_seek:.2f}")

        return DiskScheduleResult(
            algorithm_name=name,
            initial_head=initial_head,
            seek_sequence=full_seq,
            individual_seeks=seeks,
            total_head_movement=thm,
            avg_seek_distance=avg_seek
        )

    # -------------------------------------------------------------
    # 1. FCFS (First-Come, First-Served)
    # -------------------------------------------------------------
    def schedule_fcfs(self, requests: List[int], initial_head: int) -> DiskScheduleResult:
        self._validate_inputs(requests, initial_head)
        return self._build_result("FCFS", initial_head, list(requests))

    # -------------------------------------------------------------
    # 2. SSTF (Shortest Seek Time First)
    # -------------------------------------------------------------
    def schedule_sstf(self, requests: List[int], initial_head: int) -> DiskScheduleResult:
        self._validate_inputs(requests, initial_head)
        unvisited = list(requests)
        current = initial_head
        seq = []

        while unvisited:
            closest = min(unvisited, key=lambda r: (abs(r - current), r))
            seq.append(closest)
            unvisited.remove(closest)
            current = closest

        return self._build_result("SSTF", initial_head, seq)

    # -------------------------------------------------------------
    # 3. SCAN (Elevator Algorithm)
    # direction: "high" (towards max_cylinder) or "low" (towards 0)
    # -------------------------------------------------------------
    def schedule_scan(self, requests: List[int], initial_head: int, direction: str = "high") -> DiskScheduleResult:
        self._validate_inputs(requests, initial_head)
        reqs = list(set(requests))
        below = sorted([r for r in reqs if r < initial_head])
        above = sorted([r for r in reqs if r >= initial_head])
        seq = []

        if direction.lower() == "high":
            seq.extend(above)
            if below:  # Only touch boundary if requests exist in opposite direction
                if not above or above[-1] != self.max_cylinder:
                    seq.append(self.max_cylinder)
                seq.extend(reversed(below))
        else:
            seq.extend(reversed(below))
            if above:
                if not below or below[0] != 0:
                    seq.append(0)
                seq.extend(above)

        return self._build_result(f"SCAN ({direction})", initial_head, seq)

    # -------------------------------------------------------------
    # 4. C-SCAN (Circular SCAN)
    # -------------------------------------------------------------
    def schedule_cscan(self, requests: List[int], initial_head: int, direction: str = "high") -> DiskScheduleResult:
        self._validate_inputs(requests, initial_head)
        reqs = list(set(requests))
        below = sorted([r for r in reqs if r < initial_head])
        above = sorted([r for r in reqs if r >= initial_head])
        seq = []

        if direction.lower() == "high":
            seq.extend(above)
            if below:
                if not above or above[-1] != self.max_cylinder:
                    seq.append(self.max_cylinder)
                seq.append(0)
                seq.extend(below)
        else:
            seq.extend(reversed(below))
            if above:
                if not below or below[0] != 0:
                    seq.append(0)
                seq.append(self.max_cylinder)
                seq.extend(reversed(above))

        return self._build_result(f"C-SCAN ({direction})", initial_head, seq)

    # -------------------------------------------------------------
    # 5. LOOK
    # -------------------------------------------------------------
    def schedule_look(self, requests: List[int], initial_head: int, direction: str = "high") -> DiskScheduleResult:
        self._validate_inputs(requests, initial_head)
        reqs = list(set(requests))
        below = sorted([r for r in reqs if r < initial_head])
        above = sorted([r for r in reqs if r >= initial_head])
        seq = []

        if direction.lower() == "high":
            seq.extend(above)
            seq.extend(reversed(below))
        else:
            seq.extend(reversed(below))
            seq.extend(above)

        return self._build_result(f"LOOK ({direction})", initial_head, seq)

    # -------------------------------------------------------------
    # 6. C-LOOK (Circular LOOK)
    # -------------------------------------------------------------
    def schedule_clook(self, requests: List[int], initial_head: int, direction: str = "high") -> DiskScheduleResult:
        self._validate_inputs(requests, initial_head)
        reqs = list(set(requests))
        below = sorted([r for r in reqs if r < initial_head])
        above = sorted([r for r in reqs if r >= initial_head])
        seq = []

        if direction.lower() == "high":
            seq.extend(above)
            seq.extend(below)
        else:
            seq.extend(reversed(below))
            seq.extend(reversed(above))

        return self._build_result(f"C-LOOK ({direction})", initial_head, seq)
