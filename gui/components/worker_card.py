import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading


class WorkerCard(ttk.Frame):
    def __init__(self, parent, worker_id):
        super().__init__(parent, bootstyle="secondary", padding=10)
        self.stop_event = threading.Event()

        self.stats_frame = ttk.Frame(self, width=300, bootstyle="secondary")
        self.stats_frame.pack(side=LEFT, fill=Y)
        self.stats_frame.pack_propagate(False)

        title_row = ttk.Frame(self.stats_frame, bootstyle="secondary")
        title_row.pack(fill=X, anchor=W)

        self.title_label = ttk.Label(title_row, text=f"Worker #{worker_id}: Idle", font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side=LEFT)

        self.close_btn = ttk.Button(title_row, text="✕", bootstyle="danger-link", command=self.close_worker)
        self.close_btn.pack(side=RIGHT)

        self.stop_btn = ttk.Button(title_row, text="Stop", bootstyle="danger-outline", padding=(2, 0),
                                   command=self.stop_worker)
        self.stop_btn.pack(side=RIGHT, padx=5)

        self.progress_text = ttk.Label(self.stats_frame, text="Processed: 0/0")
        self.progress_text.pack(anchor=W, pady=5)

        self.progress_bar = ttk.Progressbar(self.stats_frame, bootstyle="success", mode="determinate")
        self.progress_bar.pack(fill=X, pady=5)

        self.status_label = ttk.Label(self.stats_frame, text="Waiting...", font=("Segoe UI", 8), wraplength=280)
        self.status_label.pack(anchor=W)

        log_frame = ttk.Frame(self)
        log_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        self.log_text = ttk.Text(log_frame, height=8, font=("Consolas", 8), state=DISABLED)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scroll.set)

    def stop_worker(self):
        self.stop_event.set()
        self.stop_btn.config(state=DISABLED, text="Stopping...")
        self.update_log("Stop requested. Worker will exit cleanly after the current video finishes.")

    def close_worker(self):
        self.stop_event.set()
        self.destroy()

    def update_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)
        self.log_text.config(state="disabled")

    def update_ui_state(self, title=None, progress=None, status=None, bar_val=None):
        if title: self.title_label.config(text=title)
        if progress: self.progress_text.config(text=progress)
        if status: self.status_label.config(text=status)
        if bar_val is not None: self.progress_bar["value"] = bar_val