"""
Unit tests for Disk Scheduling algorithms in OS-SimBench.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.disk_scheduler import DiskScheduler

class TestDiskScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = DiskScheduler(max_cylinder=199)
        # Textbook Silberschatz sequence: 98, 183, 37, 122, 14, 124, 65, 67 from head 53
        self.requests = [98, 183, 37, 122, 14, 124, 65, 67]
        self.initial_head = 53

    def test_fcfs_thm(self):
        res = self.scheduler.schedule_fcfs(self.requests, self.initial_head)
        # Silberschatz textbook answer: 640 cylinders
        self.assertEqual(res.total_head_movement, 640)

    def test_sstf_thm(self):
        res = self.scheduler.schedule_sstf(self.requests, self.initial_head)
        # Silberschatz textbook answer: 236 cylinders
        self.assertEqual(res.total_head_movement, 236)

    def test_scan_thm(self):
        # SCAN towards high: 53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 199 -> 37 -> 14
        # Total = (199 - 53) + (199 - 14) = 146 + 185 = 331 (if touches 199) or without redundant turn
        res = self.scheduler.schedule_scan(self.requests, self.initial_head, direction="high")
        self.assertEqual(res.total_head_movement, (199 - 53) + (199 - 14))

    def test_look_thm(self):
        # LOOK towards high: doesn't go to 199, turns at 183!
        # Total = (183 - 53) + (183 - 14) = 130 + 169 = 299
        res = self.scheduler.schedule_look(self.requests, self.initial_head, direction="high")
        self.assertEqual(res.total_head_movement, (183 - 53) + (183 - 14))

    def test_clook_thm(self):
        # C-LOOK towards high: 53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 14 -> 37
        # Total = (183 - 53) + (183 - 14) + (37 - 14) = 130 + 169 + 23 = 322
        res = self.scheduler.schedule_clook(self.requests, self.initial_head, direction="high")
        self.assertEqual(res.total_head_movement, 322)

if __name__ == '__main__':
    unittest.main()
