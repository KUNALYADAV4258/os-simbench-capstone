"""
Module: pcb.py
Defines the Process Control Block (PCB) and process lifecycle states for OS-SimBench.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any
import copy

class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"

@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0
    remaining_time: int = 0
    memory_size: int = 0
    pages: List[int] = field(default_factory=list)
    allocated_resources: List[int] = field(default_factory=list)
    max_resources: List[int] = field(default_factory=list)
    disk_requests: List[int] = field(default_factory=list)
    
    # Scheduling Metrics
    state: ProcessState = ProcessState.NEW
    start_time: int = -1
    completion_time: int = 0
    turnaround_time: int = 0
    waiting_time: int = 0
    response_time: int = -1
    queue_level: int = 0  # Used by MLFQ

    def __post_init__(self):
        if self.remaining_time <= 0:
            self.remaining_time = self.burst_time
        self.validate()

    def validate(self):
        """Validates process constraints for simulation integrity."""
        if not self.pid or not isinstance(self.pid, str):
            raise ValueError(f"Invalid PID: '{self.pid}'. PID must be a non-empty string.")
        if self.arrival_time < 0:
            raise ValueError(f"Process {self.pid}: Arrival time cannot be negative ({self.arrival_time}).")
        if self.burst_time <= 0:
            raise ValueError(f"Process {self.pid}: Burst time must be strictly positive ({self.burst_time}).")
        if self.priority < 0:
            raise ValueError(f"Process {self.pid}: Priority cannot be negative ({self.priority}).")
        if self.memory_size < 0:
            raise ValueError(f"Process {self.pid}: Memory size cannot be negative ({self.memory_size}).")

    def reset(self):
        """Resets dynamic metrics for running under a different scheduler."""
        self.remaining_time = self.burst_time
        self.state = ProcessState.NEW
        self.start_time = -1
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.response_time = -1
        self.queue_level = 0

    def clone(self) -> 'Process':
        """Creates an independent deep copy of the process."""
        return copy.deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        """Converts PCB into a serializable dictionary."""
        return {
            "pid": self.pid,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "completion_time": self.completion_time,
            "turnaround_time": self.turnaround_time,
            "waiting_time": self.waiting_time,
            "response_time": self.response_time,
            "state": self.state.value
        }
