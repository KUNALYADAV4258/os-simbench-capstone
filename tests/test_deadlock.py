"""
Unit tests for Deadlock Avoidance and Banker's Algorithm in OS-SimBench.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.deadlock import DeadlockManager

class TestDeadlockManager(unittest.TestCase):
    def setUp(self):
        # Silberschatz textbook example: 5 processes, 3 resource types (A, B, C)
        self.processes = ["P0", "P1", "P2", "P3", "P4"]
        self.available = [3, 3, 2]
        self.allocation = [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2]
        ]
        self.max = [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3]
        ]
        self.dm = DeadlockManager(self.processes, self.available, self.max, self.allocation)

    def test_banker_safety(self):
        res = self.dm.check_safety()
        self.assertTrue(res.is_safe)
        # Textbook safe sequence starts with P1 or P3
        self.assertIn(res.safe_sequence[0], ["P1", "P3"])
        self.assertEqual(len(res.safe_sequence), 5)

    def test_valid_resource_request(self):
        # P1 requests (1, 0, 2) - should be granted safely
        res = self.dm.request_resources("P1", [1, 0, 2])
        self.assertTrue(res.granted)
        self.assertTrue(res.is_safe)

    def test_request_exceeds_need(self):
        # P1 has need [1, 2, 2]. Request [2, 0, 0] exceeds claim on A!
        res = self.dm.request_resources("P1", [2, 0, 0])
        self.assertFalse(res.granted)
        self.assertIn("exceeded", res.reason.lower())

    def test_request_leading_to_unsafe_state_rollback(self):
        # P0 requests [0, 3, 0]. Available B becomes 0, so no process can satisfy its Need.
        # System detects unsafe state and rolls back!
        res = self.dm.request_resources("P0", [0, 3, 0])
        self.assertFalse(res.granted)
        self.assertIn("unsafe", res.reason.lower())
        # Verify rollback occurred (available remains [3, 3, 2])
        self.assertEqual(self.dm.available, [3, 3, 2])

    def test_wait_for_graph_cycle(self):
        # Graph with cycle: P0 -> P1 -> P2 -> P0
        adj = {
            "P0": ["P1"],
            "P1": ["P2"],
            "P2": ["P0"],
            "P3": []
        }
        has_cycle, cycles = DeadlockManager.detect_wait_for_cycles(adj)
        self.assertTrue(has_cycle)
        self.assertGreater(len(cycles), 0)

if __name__ == '__main__':
    unittest.main()
