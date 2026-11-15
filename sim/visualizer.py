"""
Module: visualizer.py
Provides visualization tools for OS-SimBench:
- Rich terminal tables (tabulate with pure-Python fallback)
- Terminal ASCII Gantt charts
- High-resolution Matplotlib graphs (Gantt, comparison bars, page fault curves, disk trajectories)
"""

import os
import tempfile
from typing import List, Tuple, Dict, Any, Optional

# Ensure headless Matplotlib with writable config directory
os.environ.setdefault('MPLCONFIGDIR', tempfile.gettempdir())
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

class Visualizer:
    @staticmethod
    def render_table(headers: List[str], rows: List[List[Any]], title: Optional[str] = None) -> str:
        """Renders a tabular layout using tabulate or pure-Python fallback."""
        output = []
        if title:
            output.append(f"\n=== {title} ===")

        if TABULATE_AVAILABLE:
            output.append(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            # Clean pure-Python ASCII table formatter
            str_rows = [[str(cell) for cell in row] for row in rows]
            col_widths = [len(h) for h in headers]
            for row in str_rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(cell))

            sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
            header_str = "|" + "|".join(f" {headers[i].center(col_widths[i])} " for i in range(len(headers))) + "|"
            
            output.append(sep)
            output.append(header_str)
            output.append(sep)
            for row in str_rows:
                row_str = "|" + "|".join(f" {row[i].ljust(col_widths[i])} " for i in range(len(row))) + "|"
                output.append(row_str)
            output.append(sep)

        return "\n".join(output)

    @staticmethod
    def render_ascii_gantt(gantt_slices: List[Tuple[int, int, str]]) -> str:
        """Renders an ASCII representation of the CPU execution Gantt chart."""
        if not gantt_slices:
            return "[Empty Timeline]"

        bar_parts = []
        time_parts = [str(gantt_slices[0][0])]

        for start, end, pid in gantt_slices:
            duration = end - start
            width = max(len(pid) + 2, duration * 2)
            label = pid.center(width)
            bar_parts.append(f"|{label}")
            time_parts.append(str(end).rjust(width + 1))

        bar_line = "".join(bar_parts) + "|"
        time_line = "".join(time_parts)

        return f"\nGantt Chart:\n{bar_line}\n{time_line}\n"

    @staticmethod
    def plot_cpu_gantt(gantt_slices: List[Tuple[int, int, str]], output_path: str, title: str = "CPU Execution Gantt Chart") -> Optional[str]:
        if not MATPLOTLIB_AVAILABLE:
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fig, ax = plt.subplots(figsize=(10, 3.5))

        unique_pids = sorted(list(set(pid for _, _, pid in gantt_slices if pid != "IDLE")))
        color_map = plt.cm.get_cmap('tab10', max(len(unique_pids), 1))
        pid_colors = {pid: color_map(i) for i, pid in enumerate(unique_pids)}
        pid_colors["IDLE"] = "#d3d3d3"

        for start, end, pid in gantt_slices:
            duration = end - start
            ax.barh(y=0, width=duration, left=start, height=0.5,
                    color=pid_colors.get(pid, "skyblue"), edgecolor='black', linewidth=1)
            ax.text(start + duration / 2, 0, pid, ha='center', va='center',
                    color='black' if pid == "IDLE" else 'white', fontweight='bold', fontsize=9)

        max_time = max(end for _, end, _ in gantt_slices) if gantt_slices else 10
        ax.set_xlim(0, max_time + 1)
        ax.set_ylim(-0.5, 0.5)
        ax.set_yticks([])
        ax.set_xlabel("Simulation Time Units (Ticks)")
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.grid(axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()

        fig.savefig(output_path, dpi=200)
        plt.close(fig)
        return output_path

    @staticmethod
    def plot_cpu_comparison(results: List[Any], output_path: str) -> Optional[str]:
        if not MATPLOTLIB_AVAILABLE or not results:
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fig, ax = plt.subplots(figsize=(11, 5.5))

        algorithms = [r.algorithm_name for r in results]
        avg_wts = [r.avg_waiting_time for r in results]
        avg_tats = [r.avg_turnaround_time for r in results]

        x = range(len(algorithms))
        width = 0.35

        rects1 = ax.bar([i - width/2 for i in x], avg_wts, width, label='Avg Waiting Time', color='#3498db')
        rects2 = ax.bar([i + width/2 for i in x], avg_tats, width, label='Avg Turnaround Time', color='#e74c3c')

        ax.set_ylabel('Time Units (Ticks)')
        ax.set_title('Comparative CPU Scheduling Performance (Lower is Better)', fontsize=12, fontweight='bold')
        ax.set_xticks(list(x))
        ax.set_xticklabels(algorithms, rotation=15, ha='right')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for rects in [rects1, rects2]:
            for rect in rects:
                h = rect.get_height()
                ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        fig.savefig(output_path, dpi=200)
        plt.close(fig)
        return output_path

    @staticmethod
    def plot_page_fault_curves(curves_dict: Dict[str, Dict[int, int]], output_path: str) -> Optional[str]:
        """Plots page faults across frame counts for multiple algorithms."""
        if not MATPLOTLIB_AVAILABLE or not curves_dict:
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fig, ax = plt.subplots(figsize=(9, 5))

        markers = ['o', 's', '^', 'D', 'v']
        colors = ['#e74c3c', '#2ecc71', '#3498db', '#f39c12', '#9b59b6']

        for idx, (algo_name, faults_map) in enumerate(curves_dict.items()):
            frames = sorted(faults_map.keys())
            faults = [faults_map[f] for f in frames]
            ax.plot(frames, faults, marker=markers[idx % len(markers)],
                    color=colors[idx % len(colors)], linewidth=2, label=algo_name)

        ax.set_xlabel('Allocated Frames')
        ax.set_ylabel('Total Page Faults')
        ax.set_title('Page Faults vs. Frame Allocation (Page Replacement)', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

        fig.savefig(output_path, dpi=200)
        plt.close(fig)
        return output_path

    @staticmethod
    def plot_disk_trajectories(results: List[Any], output_path: str) -> Optional[str]:
        """Plots head trajectories across cylinders for disk scheduling algorithms."""
        if not MATPLOTLIB_AVAILABLE or not results:
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fig, ax = plt.subplots(figsize=(10, 5.5))

        colors = ['#1abc9c', '#e67e22', '#9b59b6', '#34495e', '#e74c3c', '#2980b9']

        for idx, res in enumerate(results):
            steps = list(range(len(res.seek_sequence)))
            cylinders = res.seek_sequence
            label = f"{res.algorithm_name} (THM: {res.total_head_movement})"
            ax.plot(cylinders, steps, marker='o', linewidth=1.8,
                    color=colors[idx % len(colors)], label=label)

        ax.set_xlabel('Cylinder / Track Number')
        ax.set_ylabel('Service Order Step')
        ax.set_title('Disk Head Trajectories & Seek Progression', fontsize=12, fontweight='bold')
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

        fig.savefig(output_path, dpi=200)
        plt.close(fig)
        return output_path
