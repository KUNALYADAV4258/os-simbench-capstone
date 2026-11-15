"""
Module: web_server.py
Standalone HTTP server providing REST API endpoints and serving the OS-SimBench Web UI.
Uses standard Python library (http.server) with ZERO external backend dependencies.
"""

import os
import sys
import json
import platform
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sim.pcb import Process
from sim.cpu_scheduler import CPUScheduler
from sim.memory_manager import MemoryManager
from sim.deadlock import DeadlockManager
from sim.disk_scheduler import DiskScheduler
from sim.logger import get_sim_logger

WEB_DIR = os.path.join(BASE_DIR, "web")
CHARTS_DIR = os.path.join(BASE_DIR, "reports", "charts")

class SimBenchAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw_data = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw_data)

    def _send_json(self, data: Any, status: int = 200):
        self._set_headers(status, "application/json")
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_error(self, message: str, status: int = 400):
        self._set_headers(status, "application/json")
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/presets":
            self._handle_get_presets()
        elif path == "/api/system":
            self._handle_get_system()
        elif path.startswith("/charts/"):
            # Serve generated chart images
            chart_filename = os.path.basename(path)
            chart_path = os.path.join(CHARTS_DIR, chart_filename)
            if os.path.exists(chart_path):
                self._set_headers(200, "image/png")
                with open(chart_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Chart not found")
        elif path == "/" or not os.path.exists(os.path.join(WEB_DIR, path.lstrip("/"))):
            # Fallback to index.html for SPA routing
            index_path = os.path.join(WEB_DIR, "index.html")
            if os.path.exists(index_path):
                self._set_headers(200, "text/html; charset=utf-8")
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = self._read_json_body()
            if path == "/api/cpu/run":
                self._handle_cpu_run(body)
            elif path == "/api/memory/run":
                self._handle_memory_run(body)
            elif path == "/api/memory/belady":
                self._handle_memory_belady(body)
            elif path == "/api/memory/contiguous":
                self._handle_memory_contiguous(body)
            elif path == "/api/deadlock/safety":
                self._handle_deadlock_safety(body)
            elif path == "/api/deadlock/request":
                self._handle_deadlock_request(body)
            elif path == "/api/disk/run":
                self._handle_disk_run(body)
            elif path == "/api/pipeline/run":
                self._handle_pipeline_run(body)
            else:
                self._send_error(f"Unknown endpoint: {path}", status=404)
        except Exception as e:
            self._send_error(f"Execution Error: {str(e)}", status=500)

    # -------------------------------------------------------------
    # Route Handlers
    # -------------------------------------------------------------
    def _handle_get_presets(self):
        try:
            with open(os.path.join(BASE_DIR, "data", "cpu_workloads.json"), "r") as f:
                cpu_presets = json.load(f)
            with open(os.path.join(BASE_DIR, "data", "memory_traces.json"), "r") as f:
                mem_presets = json.load(f)
            with open(os.path.join(BASE_DIR, "data", "deadlock_scenarios.json"), "r") as f:
                dl_presets = json.load(f)
            with open(os.path.join(BASE_DIR, "data", "disk_workloads.json"), "r") as f:
                disk_presets = json.load(f)

            self._send_json({
                "cpu": cpu_presets,
                "memory": mem_presets,
                "deadlock": dl_presets,
                "disk": disk_presets
            })
        except Exception as e:
            self._send_error(str(e))

    def _handle_get_system(self):
        self._send_json({
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count() or 1,
            "architecture": platform.machine()
        })

    def _handle_cpu_run(self, body: Dict[str, Any]):
        procs_raw = body.get("processes", [])
        if not procs_raw:
            return self._send_error("Process list cannot be empty.")

        quantum = int(body.get("quantum", 2))
        q0_q = int(body.get("q0_quantum", 2))
        q1_q = int(body.get("q1_quantum", 4))
        aging = int(body.get("aging_interval", 15))

        processes = [
            Process(
                pid=str(p["pid"]),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 0))
            )
            for p in procs_raw
        ]

        scheduler = CPUScheduler()
        results = [
            scheduler.schedule_fcfs(processes),
            scheduler.schedule_sjf(processes),
            scheduler.schedule_srtf(processes),
            scheduler.schedule_priority(processes),
            scheduler.schedule_priority_preemptive(processes),
            scheduler.schedule_round_robin(processes, quantum=quantum),
            scheduler.schedule_mlfq(processes, q0_quantum=q0_q, q1_quantum=q1_q, aging_interval=aging)
        ]

        out = []
        for r in results:
            out.append({
                "algorithm": r.algorithm_name,
                "total_time": r.total_time,
                "idle_time": r.idle_time,
                "cpu_utilization": round(r.cpu_utilization, 2),
                "avg_tat": round(r.avg_turnaround_time, 2),
                "avg_wt": round(r.avg_waiting_time, 2),
                "avg_rt": round(r.avg_response_time, 2),
                "throughput": round(r.throughput, 4),
                "gantt": [{"start": g[0], "end": g[1], "pid": g[2]} for g in r.gantt_chart],
                "processes": [p.to_dict() for p in r.processes]
            })

        self._send_json({"results": out})

    def _handle_memory_run(self, body: Dict[str, Any]):
        ref_string = body.get("reference_string", [])
        num_frames = int(body.get("num_frames", 3))

        if not ref_string:
            return self._send_error("Reference string is required.")

        mm = MemoryManager()
        results = [
            mm.fifo_page_replacement(ref_string, num_frames),
            mm.lru_page_replacement(ref_string, num_frames),
            mm.optimal_page_replacement(ref_string, num_frames),
            mm.clock_page_replacement(ref_string, num_frames)
        ]

        out = []
        for r in results:
            out.append({
                "algorithm": r.algorithm_name,
                "frames": r.num_frames,
                "total_refs": r.total_references,
                "page_faults": r.page_faults,
                "page_hits": r.page_hits,
                "fault_rate": round(r.fault_rate, 2),
                "hit_rate": round(r.hit_rate, 2),
                "steps": [
                    {
                        "step": s.step_num,
                        "page": s.page,
                        "hit": s.hit,
                        "evicted": s.evicted,
                        "frames": s.frames_snapshot
                    }
                    for s in r.steps
                ]
            })

        # Frame range sensitivity (2 to 7 frames)
        sensitivity = {"FIFO": {}, "LRU": {}, "Optimal": {}, "Clock": {}}
        for f in range(2, 8):
            sensitivity["FIFO"][f] = mm.fifo_page_replacement(ref_string, f).page_faults
            sensitivity["LRU"][f] = mm.lru_page_replacement(ref_string, f).page_faults
            sensitivity["Optimal"][f] = mm.optimal_page_replacement(ref_string, f).page_faults
            sensitivity["Clock"][f] = mm.clock_page_replacement(ref_string, f).page_faults

        self._send_json({"results": out, "sensitivity": sensitivity})

    def _handle_memory_belady(self, body: Dict[str, Any]):
        ref_string = body.get("reference_string", [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5])
        mm = MemoryManager()
        anomaly = mm.check_beladys_anomaly(ref_string, frame_range=(3, 4))
        self._send_json(anomaly)

    def _handle_memory_contiguous(self, body: Dict[str, Any]):
        blocks = body.get("blocks", [100, 500, 200, 300, 600])
        requests = body.get("requests", {"P1": 212, "P2": 417, "P3": 112, "P4": 426})
        mm = MemoryManager()

        out = {}
        for algo in ["first_fit", "best_fit", "worst_fit"]:
            res = mm.allocate_contiguous(blocks, requests, algo)
            out[algo] = {
                "name": res.algorithm_name,
                "allocations": res.allocations,
                "remaining_blocks": res.remaining_blocks,
                "internal_fragmentation": res.internal_fragmentation,
                "external_fragmentation": res.external_fragmentation,
                "unallocated": res.unallocated_procs
            }
        self._send_json({"results": out, "blocks": blocks, "requests": requests})

    def _handle_deadlock_safety(self, body: Dict[str, Any]):
        pids = body.get("processes", [])
        avail = body.get("available", [])
        max_m = body.get("max", [])
        alloc = body.get("allocation", [])

        dm = DeadlockManager(pids, avail, max_m, alloc)
        safety_res = dm.check_safety()

        self._send_json({
            "is_safe": safety_res.is_safe,
            "safe_sequence": safety_res.safe_sequence,
            "trace": safety_res.trace,
            "need": dm.need,
            "available": dm.available,
            "allocation": dm.allocation,
            "max": dm.max_matrix,
            "processes": dm.process_ids
        })

    def _handle_deadlock_request(self, body: Dict[str, Any]):
        pids = body.get("processes", [])
        avail = body.get("available", [])
        max_m = body.get("max", [])
        alloc = body.get("allocation", [])
        pid = body.get("pid")
        req = body.get("request", [])

        dm = DeadlockManager(pids, avail, max_m, alloc)
        req_res = dm.request_resources(pid, req)

        self._send_json({
            "granted": req_res.granted,
            "reason": req_res.reason,
            "is_safe": req_res.is_safe,
            "safe_sequence": req_res.safe_sequence,
            "updated_state": req_res.system_state
        })

    def _handle_disk_run(self, body: Dict[str, Any]):
        requests = body.get("requests", [])
        head = int(body.get("initial_head", 53))
        direction = body.get("direction", "high")
        max_cyl = int(body.get("max_cylinder", 199))

        if not requests:
            return self._send_error("Disk request queue cannot be empty.")

        ds = DiskScheduler(max_cylinder=max_cyl)
        results = [
            ds.schedule_fcfs(requests, head),
            ds.schedule_sstf(requests, head),
            ds.schedule_scan(requests, head, direction),
            ds.schedule_cscan(requests, head, direction),
            ds.schedule_look(requests, head, direction),
            ds.schedule_clook(requests, head, direction)
        ]

        out = []
        for r in results:
            out.append({
                "algorithm": r.algorithm_name,
                "initial_head": r.initial_head,
                "total_head_movement": r.total_head_movement,
                "avg_seek_distance": round(r.avg_seek_distance, 2),
                "seek_sequence": r.seek_sequence,
                "individual_seeks": r.individual_seeks
            })

        self._send_json({"results": out, "requests": requests, "initial_head": head, "max_cylinder": max_cyl})

    def _handle_pipeline_run(self, body: Dict[str, Any]):
        p = Process(
            pid=body.get("pid", "JOB_WEB_1"),
            arrival_time=0,
            burst_time=int(body.get("burst_time", 6)),
            priority=int(body.get("priority", 1)),
            pages=body.get("pages", [2, 4, 1, 2, 5, 2]),
            allocated_resources=body.get("allocated_resources", [1, 0, 1]),
            max_resources=body.get("max_resources", [2, 1, 2]),
            disk_requests=body.get("disk_requests", [45, 120, 85])
        )

        steps = []
        steps.append({"step": 1, "title": "PCB Initialized", "detail": f"Process {p.pid} created with burst={p.burst_time}, pages={p.pages}, disk I/O={p.disk_requests}."})

        # Memory
        mm = MemoryManager()
        mem_res = mm.lru_page_replacement(p.pages, num_frames=3)
        steps.append({"step": 2, "title": "Memory Paging (LRU)", "detail": f"3 frames allocated. Faults: {mem_res.page_faults}, Hits: {mem_res.page_hits} (Hit Rate: {mem_res.hit_rate:.1f}%)."})

        # Deadlock
        dm = DeadlockManager(
            process_ids=[p.pid, "DAEMON_1"],
            available=[2, 2, 1],
            max_matrix=[p.max_resources, [1, 1, 1]],
            allocation_matrix=[p.allocated_resources, [0, 1, 0]]
        )
        safe = dm.check_safety()
        steps.append({"step": 3, "title": "Banker's Safety Check", "detail": f"Safety verified? {safe.is_safe} Sequence: <{' -> '.join(safe.safe_sequence)}>."})

        # CPU
        sched = CPUScheduler()
        cpu_res = sched.schedule_round_robin([p], quantum=2)
        steps.append({"step": 4, "title": "CPU Dispatch (Round Robin)", "detail": f"Completed at tick {p.completion_time}. Total Time: {cpu_res.total_time}."})

        # Disk
        ds = DiskScheduler(max_cylinder=199)
        disk_res = ds.schedule_sstf(p.disk_requests, initial_head=50)
        steps.append({"step": 5, "title": "Disk I/O Servicing (SSTF)", "detail": f"Serviced {p.disk_requests} with {disk_res.total_head_movement} head movements (Path: {' -> '.join(map(str, disk_res.seek_sequence))})."})

        steps.append({"step": 6, "title": "Termination", "detail": f"Process {p.pid} exited with state TERMINATED. Resources returned to system."})

        self._send_json({"process": p.to_dict(), "steps": steps})

def run_server(host: str = "0.0.0.0", port: int = 8080):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, SimBenchAPIHandler)
    print("\n" + "="*65)
    print("   OS-SimBench Web Server Running Successfully!")
    print(f"   Local URL:   http://localhost:{port}")
    print(f"   Network URL: http://{host}:{port}")
    print("   Press Ctrl+C to stop the server.")
    print("="*65 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down OS-SimBench server...")
        httpd.server_close()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port)
