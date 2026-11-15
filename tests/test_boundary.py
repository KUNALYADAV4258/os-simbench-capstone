"""
Boundary and Reliability Unit Tests for OS-SimBench.
Fulfills Phase 4 requirements: tests invalid, negative, and extreme inputs.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.pcb import Process
from sim.cpu_scheduler import CPUScheduler
from sim.memory_manager import MemoryManager
from sim.deadlock import DeadlockManager
from sim.disk_scheduler import DiskScheduler

class TestBoundaryAndReliability(unittest.TestCase):
    def test_invalid_negative_burst_time(self):
        with self.assertRaises(ValueError):
            Process(pid="P_ERR", arrival_time=0, burst_time=-5)

    def test_invalid_zero_burst_time(self):
        with self.assertRaises(ValueError):
            Process(pid="P_ERR", arrival_time=0, burst_time=0)

    def test_invalid_negative_arrival_time(self):
        with self.assertRaises(ValueError):
            Process(pid="P_ERR", arrival_time=-2, burst_time=5)

    def test_invalid_round_robin_zero_quantum(self):
        scheduler = CPUScheduler()
        procs = [Process(pid="P1", arrival_time=0, burst_time=5)]
        with self.assertRaises(ValueError):
            scheduler.schedule_round_robin(procs, quantum=0)

    def test_empty_process_list(self):
        scheduler = CPUScheduler()
        with self.assertRaises(ValueError):
            scheduler.schedule_fcfs([])

    def test_zero_frames_memory(self):
        mm = MemoryManager()
        with self.assertRaises(ValueError):
            mm.fifo_page_replacement([1, 2, 3], num_frames=0)

    def test_empty_page_reference_string(self):
        mm = MemoryManager()
        with self.assertRaises(ValueError):
            mm.lru_page_replacement([], num_frames=3)

    def test_disk_out_of_bounds_cylinder(self):
        ds = DiskScheduler(max_cylinder=199)
        with self.assertRaises(ValueError):
            ds.schedule_fcfs([50, 250], initial_head=53)

    def test_disk_negative_head(self):
        ds = DiskScheduler(max_cylinder=199)
        with self.assertRaises(ValueError):
            ds.schedule_fcfs([50, 70], initial_head=-1)

    def test_deadlock_mismatched_dimensions(self):
        with self.assertRaises(ValueError):
            DeadlockManager(
                process_ids=["P0", "P1"],
                available=[1, 2],
                max_matrix=[[2, 2]],  # Only 1 row for 2 processes
                allocation_matrix=[[1, 1], [0, 0]]
            )

    def test_deadlock_allocation_exceeds_max(self):
        with self.assertRaises(ValueError):
            DeadlockManager(
                process_ids=["P0"],
                available=[1, 1],
                max_matrix=[[2, 2]],
                allocation_matrix=[[3, 1]]  # Allocation > Max
            )

if __name__ == '__main__':
    unittest.main()
