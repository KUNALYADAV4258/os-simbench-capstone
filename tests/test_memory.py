"""
Unit tests for Memory Management algorithms in OS-SimBench.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.memory_manager import MemoryManager

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.mm = MemoryManager()
        # Silberschatz textbook reference string
        self.ref_string = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]

    def test_fifo_fault_count(self):
        res = self.mm.fifo_page_replacement(self.ref_string, num_frames=3)
        # Textbook Silberschatz answer for FIFO with 3 frames: 15 page faults
        self.assertEqual(res.page_faults, 15)
        self.assertEqual(res.page_hits, 5)

    def test_lru_fault_count(self):
        res = self.mm.lru_page_replacement(self.ref_string, num_frames=3)
        # Textbook Silberschatz answer for LRU with 3 frames: 12 page faults
        self.assertEqual(res.page_faults, 12)
        self.assertEqual(res.page_hits, 8)

    def test_optimal_fault_count(self):
        res = self.mm.optimal_page_replacement(self.ref_string, num_frames=3)
        # Textbook Silberschatz answer for Optimal with 3 frames: 9 page faults
        self.assertEqual(res.page_faults, 9)
        self.assertEqual(res.page_hits, 11)

    def test_clock_fault_count(self):
        res = self.mm.clock_page_replacement(self.ref_string, num_frames=3)
        self.assertLessEqual(res.page_faults, 15)

    def test_beladys_anomaly(self):
        belady_trace = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        res3 = self.mm.fifo_page_replacement(belady_trace, num_frames=3)
        res4 = self.mm.fifo_page_replacement(belady_trace, num_frames=4)
        # Belady's Anomaly: 3 frames = 9 faults; 4 frames = 10 faults!
        self.assertEqual(res3.page_faults, 9)
        self.assertEqual(res4.page_faults, 10)
        anomaly = self.mm.check_beladys_anomaly(belady_trace, (3, 4))
        self.assertTrue(anomaly["anomaly_detected"])

    def test_contiguous_allocation(self):
        blocks = [100, 500, 200, 300, 600]
        requests = {"P1": 212, "P2": 417, "P3": 112, "P4": 426}
        res_ff = self.mm.allocate_contiguous(blocks, requests, "first_fit")
        self.assertEqual(res_ff.allocations["P1"], 1)  # 500 fits 212

        res_bf = self.mm.allocate_contiguous(blocks, requests, "best_fit")
        self.assertEqual(res_bf.allocations["P1"], 3)  # 300 is closest fit to 212

if __name__ == '__main__':
    unittest.main()
