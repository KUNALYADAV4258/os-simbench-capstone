"""
Module: memory_manager.py
Implements core Memory Management algorithms for OS-SimBench:
1. Page Replacement:
   - FIFO (First-In, First-Out)
   - LRU (Least Recently Used)
   - Optimal (Belady's Min Algorithm)
   - Clock (Second Chance / Circular Queue)
2. Belady's Anomaly Detector
3. Contiguous Allocation:
   - First-Fit, Best-Fit, Worst-Fit with Fragmentation Analytics
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from sim.logger import get_sim_logger

@dataclass
class PageStep:
    step_num: int
    page: int
    hit: bool
    evicted: Optional[int]
    frames_snapshot: List[Optional[int]]

@dataclass
class PageReplacementResult:
    algorithm_name: str
    total_references: int
    num_frames: int
    page_faults: int
    page_hits: int
    fault_rate: float
    hit_rate: float
    steps: List[PageStep]

    def get_summary_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm_name,
            "num_frames": self.num_frames,
            "total_refs": self.total_references,
            "page_faults": self.page_faults,
            "page_hits": self.page_hits,
            "fault_rate": round(self.fault_rate, 2),
            "hit_rate": round(self.hit_rate, 2)
        }

@dataclass
class ContiguousAllocResult:
    algorithm_name: str
    allocations: Dict[str, Optional[int]]  # proc_id -> block_index
    block_sizes: List[int]
    remaining_blocks: List[int]
    internal_fragmentation: int
    external_fragmentation: int
    unallocated_procs: List[str]

class MemoryManager:
    def __init__(self):
        self.logger = get_sim_logger()

    def _validate_page_inputs(self, reference_string: List[int], num_frames: int):
        if not reference_string:
            raise ValueError("Page reference string cannot be empty.")
        if num_frames <= 0:
            raise ValueError(f"Number of memory frames must be positive (got {num_frames}).")

    # -------------------------------------------------------------
    # 1. FIFO (First-In, First-Out)
    # -------------------------------------------------------------
    def fifo_page_replacement(self, reference_string: List[int], num_frames: int) -> PageReplacementResult:
        self._validate_page_inputs(reference_string, num_frames)
        frames: List[Optional[int]] = [None] * num_frames
        queue = deque()  # stores pages in order of arrival
        steps: List[PageStep] = []
        faults = 0
        hits = 0

        for idx, page in enumerate(reference_string):
            if page in frames:
                hits += 1
                steps.append(PageStep(idx + 1, page, True, None, list(frames)))
            else:
                faults += 1
                evicted = None
                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                    queue.append(page)
                else:
                    evicted = queue.popleft()
                    replace_idx = frames.index(evicted)
                    frames[replace_idx] = page
                    queue.append(page)
                steps.append(PageStep(idx + 1, page, False, evicted, list(frames)))

        total = len(reference_string)
        fault_rate = (faults / total) * 100.0
        hit_rate = (hits / total) * 100.0
        self.logger.info(f"[FIFO] Frames={num_frames}, References={total}, Faults={faults}, Hits={hits}, Hit Rate={hit_rate:.1f}%")

        return PageReplacementResult("FIFO", total, num_frames, faults, hits, fault_rate, hit_rate, steps)

    # -------------------------------------------------------------
    # 2. LRU (Least Recently Used)
    # -------------------------------------------------------------
    def lru_page_replacement(self, reference_string: List[int], num_frames: int) -> PageReplacementResult:
        self._validate_page_inputs(reference_string, num_frames)
        frames: List[Optional[int]] = [None] * num_frames
        last_used: Dict[int, int] = {}  # page -> last used timestamp
        steps: List[PageStep] = []
        faults = 0
        hits = 0

        for idx, page in enumerate(reference_string):
            last_used[page] = idx
            if page in frames:
                hits += 1
                steps.append(PageStep(idx + 1, page, True, None, list(frames)))
            else:
                faults += 1
                evicted = None
                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                else:
                    # Evict page with minimum last_used timestamp
                    lru_page = min(frames, key=lambda p: last_used[p])
                    evicted = lru_page
                    replace_idx = frames.index(lru_page)
                    frames[replace_idx] = page
                steps.append(PageStep(idx + 1, page, False, evicted, list(frames)))

        total = len(reference_string)
        fault_rate = (faults / total) * 100.0
        hit_rate = (hits / total) * 100.0
        self.logger.info(f"[LRU] Frames={num_frames}, References={total}, Faults={faults}, Hits={hits}, Hit Rate={hit_rate:.1f}%")

        return PageReplacementResult("LRU", total, num_frames, faults, hits, fault_rate, hit_rate, steps)

    # -------------------------------------------------------------
    # 3. Optimal (Belady's Min Algorithm)
    # -------------------------------------------------------------
    def optimal_page_replacement(self, reference_string: List[int], num_frames: int) -> PageReplacementResult:
        self._validate_page_inputs(reference_string, num_frames)
        frames: List[Optional[int]] = [None] * num_frames
        steps: List[PageStep] = []
        faults = 0
        hits = 0
        total = len(reference_string)

        for idx, page in enumerate(reference_string):
            if page in frames:
                hits += 1
                steps.append(PageStep(idx + 1, page, True, None, list(frames)))
            else:
                faults += 1
                evicted = None
                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                else:
                    # Find page in frames that will not be used for longest time in future
                    furthest_idx = -1
                    victim = None
                    for f in frames:
                        try:
                            next_use = reference_string.index(f, idx + 1)
                        except ValueError:
                            # Never used again, perfect candidate
                            next_use = float('inf')
                        if next_use > furthest_idx:
                            furthest_idx = next_use
                            victim = f

                    evicted = victim
                    replace_idx = frames.index(victim)
                    frames[replace_idx] = page
                steps.append(PageStep(idx + 1, page, False, evicted, list(frames)))

        fault_rate = (faults / total) * 100.0
        hit_rate = (hits / total) * 100.0
        self.logger.info(f"[Optimal] Frames={num_frames}, References={total}, Faults={faults}, Hits={hits}, Hit Rate={hit_rate:.1f}%")

        return PageReplacementResult("Optimal", total, num_frames, faults, hits, fault_rate, hit_rate, steps)

    # -------------------------------------------------------------
    # 4. Clock (Second Chance Algorithm)
    # -------------------------------------------------------------
    def clock_page_replacement(self, reference_string: List[int], num_frames: int) -> PageReplacementResult:
        self._validate_page_inputs(reference_string, num_frames)
        frames: List[Optional[int]] = [None] * num_frames
        ref_bits: List[int] = [0] * num_frames
        pointer = 0
        steps: List[PageStep] = []
        faults = 0
        hits = 0

        for idx, page in enumerate(reference_string):
            if page in frames:
                hits += 1
                frame_idx = frames.index(page)
                ref_bits[frame_idx] = 1
                steps.append(PageStep(idx + 1, page, True, None, list(frames)))
            else:
                faults += 1
                evicted = None
                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                    ref_bits[empty_idx] = 1
                    pointer = (empty_idx + 1) % num_frames
                else:
                    while True:
                        if ref_bits[pointer] == 0:
                            evicted = frames[pointer]
                            frames[pointer] = page
                            ref_bits[pointer] = 1
                            pointer = (pointer + 1) % num_frames
                            break
                        else:
                            ref_bits[pointer] = 0
                            pointer = (pointer + 1) % num_frames
                steps.append(PageStep(idx + 1, page, False, evicted, list(frames)))

        total = len(reference_string)
        fault_rate = (faults / total) * 100.0
        hit_rate = (hits / total) * 100.0
        self.logger.info(f"[Clock] Frames={num_frames}, References={total}, Faults={faults}, Hits={hits}, Hit Rate={hit_rate:.1f}%")

        return PageReplacementResult("Clock (Second Chance)", total, num_frames, faults, hits, fault_rate, hit_rate, steps)

    # -------------------------------------------------------------
    # Belady's Anomaly Analysis
    # -------------------------------------------------------------
    def check_beladys_anomaly(self, reference_string: List[int] = None, frame_range: Tuple[int, int] = (3, 4)) -> Dict[str, Any]:
        """Checks whether increasing frames increases page faults under FIFO."""
        if reference_string is None:
            # Canonical Belady Anomaly trace: 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5
            reference_string = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

        f_start, f_end = frame_range
        results = {}
        for f in range(f_start, f_end + 1):
            res = self.fifo_page_replacement(reference_string, f)
            results[f] = res.page_faults

        anomaly_detected = False
        anomaly_pairs = []
        for f in range(f_start, f_end):
            if results[f + 1] > results[f]:
                anomaly_detected = True
                anomaly_pairs.append((f, results[f], f + 1, results[f + 1]))

        return {
            "anomaly_detected": anomaly_detected,
            "reference_string": reference_string,
            "faults_by_frame": results,
            "anomaly_pairs": anomaly_pairs
        }

    # -------------------------------------------------------------
    # Contiguous Allocation (First Fit, Best Fit, Worst Fit)
    # -------------------------------------------------------------
    def allocate_contiguous(self, blocks: List[int], process_requests: Dict[str, int], algorithm: str = "first_fit") -> ContiguousAllocResult:
        rem_blocks = list(blocks)
        allocations: Dict[str, Optional[int]] = {}
        unallocated = []
        internal_frag = 0

        for pid, req in process_requests.items():
            chosen_block = None

            if algorithm.lower() == "first_fit":
                for i, b in enumerate(rem_blocks):
                    if b >= req:
                        chosen_block = i
                        break
            elif algorithm.lower() == "best_fit":
                candidates = [(i, b) for i, b in enumerate(rem_blocks) if b >= req]
                if candidates:
                    chosen_block = min(candidates, key=lambda x: x[1])[0]
            elif algorithm.lower() == "worst_fit":
                candidates = [(i, b) for i, b in enumerate(rem_blocks) if b >= req]
                if candidates:
                    chosen_block = max(candidates, key=lambda x: x[1])[0]
            else:
                raise ValueError(f"Unknown allocation algorithm '{algorithm}'. Must be first_fit, best_fit, or worst_fit.")

            if chosen_block is not None:
                allocations[pid] = chosen_block
                internal_frag += (rem_blocks[chosen_block] - req)
                rem_blocks[chosen_block] -= req  # reduce available in block
            else:
                allocations[pid] = None
                unallocated.append(pid)

        # External fragmentation: sum of free fragments that cannot accommodate unallocated processes
        ext_frag = sum(b for b in rem_blocks if b > 0)

        return ContiguousAllocResult(
            algorithm_name=algorithm.replace("_", " ").title(),
            allocations=allocations,
            block_sizes=blocks,
            remaining_blocks=rem_blocks,
            internal_fragmentation=internal_frag,
            external_fragmentation=ext_frag,
            unallocated_procs=unallocated
        )
