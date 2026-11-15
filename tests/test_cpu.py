"""
Unit tests for CPU Scheduling algorithms in OS-SimBench.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.pcb import Process
from sim.cpu_scheduler import CPUScheduler

class TestCPUScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = CPUScheduler()
        self.sample_processes = [
            Process(pid="P1", arrival_time=0, burst_time=5, priority=2),
            Process(pid="P2", arrival_time=1, burst_time=3, priority=1),
            Process(pid="P3", arrival_time=2, burst_time=8, priority=4),
            Process(pid="P4", arrival_time=3, burst_time=6, priority=3),
        ]

    def test_fcfs_scheduling(self):
        res = self.scheduler.schedule_fcfs(self.sample_processes)
        self.assertEqual(res.total_time, 22)
        self.assertEqual(res.idle_time, 0)
        self.assertEqual(res.cpu_utilization, 100.0)
        # P1: CT=5, TAT=5, WT=0
        # P2: CT=8, TAT=7, WT=4
        # P3: CT=16, TAT=14, WT=6
        # P4: CT=22, TAT=19, WT=13
        p1 = next(p for p in res.processes if p.pid == "P1")
        self.assertEqual(p1.completion_time, 5)
        self.assertEqual(p1.waiting_time, 0)

    def test_sjf_non_preemptive(self):
        res = self.scheduler.schedule_sjf(self.sample_processes)
        self.assertEqual(res.total_time, 22)
        # At t=0, P1 starts (runs 0..5). At t=5, P2, P3, P4 arrived. P2 burst=3 is smallest!
        # P2 runs 5..8. Next is P4 (burst=6) runs 8..14. Next is P3 (burst=8) runs 14..22.
        p2 = next(p for p in res.processes if p.pid == "P2")
        self.assertEqual(p2.completion_time, 8)

    def test_srtf_preemptive(self):
        res = self.scheduler.schedule_srtf(self.sample_processes)
        self.assertEqual(res.total_time, 22)
        # At t=1, P2 arrives with burst 3 < remaining of P1 (4). P2 preempts!
        first_slice = res.gantt_chart[0]
        self.assertEqual(first_slice, (0, 1, "P1"))
        second_slice = res.gantt_chart[1]
        self.assertEqual(second_slice, (1, 4, "P2"))

    def test_round_robin(self):
        res = self.scheduler.schedule_round_robin(self.sample_processes, quantum=2)
        self.assertEqual(res.total_time, 22)
        self.assertGreater(len(res.gantt_chart), len(self.sample_processes))

    def test_mlfq_scheduling(self):
        res = self.scheduler.schedule_mlfq(self.sample_processes, q0_quantum=2, q1_quantum=4, aging_interval=10)
        self.assertEqual(res.total_time, 22)
        self.assertEqual(res.idle_time, 0)

if __name__ == '__main__':
    unittest.main()
