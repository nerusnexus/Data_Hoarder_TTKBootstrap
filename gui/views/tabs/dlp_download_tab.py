import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
import threading
import queue


class DownloadWorkerCard(ttk.Frame):
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
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)

    def update_ui_state(self, title=None, progress=None, status=None, bar_val=None):
        if title: self.title_label.config(text=title)
        if progress: self.progress_text.config(text=progress)
        if status: self.status_label.config(text=status)
        if bar_val is not None: self.progress_bar["value"] = bar_val


class DlpDownloadTab(ttk.Frame):
    def __init__(self, parent, add_group_service, add_channel_service, dlp_download_service):
        super().__init__(parent)
        self.add_group_service = add_group_service
        self.add_channel_service = add_channel_service
        self.dlp_download_service = dlp_download_service

        self.main_scroll = ScrolledFrame(self, autohide=True)
        self.main_scroll.pack(fill=BOTH, expand=True)

        self.worker_container = None
        self.tree = None
        self.queue_scroll = None
        self.selected_items_list = []
        self.params = {}
        self.combos = {}
        self.task_queue = queue.Queue()
        self.worker_count = 0

        self.build_ui()
        self.winfo_toplevel().bind("<<DataUpdated>>", self.refresh_tree, add="+")

    def build_ui(self):
        top_frame = ttk.Frame(self.main_scroll)
        top_frame.pack(fill=X, padx=10, pady=10)

        tree_outer = ttk.Frame(top_frame, width=300)
        tree_outer.pack(side=LEFT, fill=Y, padx=(0, 10))
        tree_outer.pack_propagate(False)
        tree_frame = ttk.Labelframe(tree_outer, text="Available Channels", padding=10)
        tree_frame.pack(fill=BOTH, expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL)
        tree_scroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(tree_frame, selectmode="extended", show="tree", yscrollcommand=tree_scroll.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<Double-1>", self.add_to_selection)
        self.load_tree_data()

        selection_outer = ttk.Frame(top_frame, width=300)
        selection_outer.pack(side=LEFT, fill=Y, padx=(0, 10))
        selection_outer.pack_propagate(False)
        selection_frame = ttk.Labelframe(selection_outer, text="Queue to Download", padding=10)
        selection_frame.pack(fill=BOTH, expand=True)
        self.queue_scroll = ScrolledFrame(selection_frame, autohide=True)
        self.queue_scroll.pack(fill=BOTH, expand=True)

        config_outer = ttk.Frame(top_frame)
        config_outer.pack(side=RIGHT, fill=BOTH, expand=True)
        config_frame = ttk.Labelframe(config_outer, text="Download Parameters", padding=10)
        config_frame.pack(fill=BOTH, expand=True)

        params_container = ttk.Frame(config_frame)
        params_container.pack(fill=BOTH, expand=True)

        left_params = ttk.Frame(params_container)
        left_params.pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        ttk.Label(left_params, text="Format Selection:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(0, 5))
        self.format_var = ttk.StringVar(value="bestvideo+bestaudio/best")
        format_cb = ttk.Combobox(left_params, textvariable=self.format_var,
                                 values=["bestvideo+bestaudio/best", "best", "bestvideo[height<=1080]+bestaudio/best",
                                         "bestaudio/best"], state="readonly")
        format_cb.pack(fill=X, pady=(0, 10))

        ttk.Label(left_params, text="Merge Container:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(0, 5))
        self.container_var = ttk.StringVar(value="mkv")
        container_cb = ttk.Combobox(left_params, textvariable=self.container_var, values=["mkv", "mp4", "webm"],
                                    state="readonly")
        container_cb.pack(fill=X, pady=(0, 10))

        ttk.Label(left_params, text="Options:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(10, 5))

        self.skip_downloaded_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(left_params, text="Skip Downloaded Media", variable=self.skip_downloaded_var).pack(anchor=W,
                                                                                                           padx=5)

        self.cookie_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(left_params, text="Use Firefox Cookies", variable=self.cookie_var).pack(anchor=W, padx=5,
                                                                                                pady=(5, 5))

        right_params = ttk.Frame(params_container)
        right_params.pack(side=RIGHT, fill=BOTH, expand=True, padx=5)
        inputs = [
            ("Workers (Threads)", "1", [str(i) for i in range(1, 17)]),
            ("--sleep-requests", "1", [str(i) for i in range(0, 11)]),
            ("--sleep-interval", "5", [str(i) for i in range(0, 61, 5)]),
            ("--max-sleep-interval", "15", [str(i) for i in range(0, 121, 10)]),
            ("--retries", "10", [str(i) for i in range(0, 101, 5)]),
            ("--fragment-retries", "10", [str(i) for i in range(0, 101, 5)])
        ]
        for label, default, vals in inputs:
            row = ttk.Frame(right_params)
            row.pack(fill=X, pady=2)
            ttk.Label(row, text=label, font=("Segoe UI", 8)).pack(side=LEFT)
            var = ttk.StringVar(value=default)
            cb = ttk.Combobox(row, textvariable=var, values=vals, state="readonly", width=8)
            cb.pack(side=RIGHT)
            self.params[label] = var
            self.combos[label] = cb

        self.start_btn = ttk.Button(config_outer, text="START DOWNLOAD", bootstyle="info",
                                    command=self.start_process)
        self.start_btn.pack(fill=X, pady=10)

        self.worker_container = ttk.Labelframe(self.main_scroll, text="Active Workers")
        self.worker_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def refresh_tree(self, _event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.load_tree_data()

    def add_to_selection(self, _event):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        item_text = self.tree.item(item_id, "text")
        if "channel" not in self.tree.item(item_id, "tags"): return
        if item_text in self.selected_items_list: return
        self.selected_items_list.append(item_text)
        self.render_selection_row(item_text)

    def render_selection_row(self, text):
        row = ttk.Frame(self.queue_scroll, padding=2)
        row.pack(fill=X)
        ttk.Label(row, text=text, font=("Segoe UI", 9)).pack(side=LEFT, padx=5)
        ttk.Button(row, text="✕", bootstyle="danger-link",
                   command=lambda r=row, t=text: self.remove_from_selection(r, t)).pack(side=RIGHT)

    def remove_from_selection(self, row_widget, text):
        if text in self.selected_items_list: self.selected_items_list.remove(text)
        row_widget.destroy()

    def load_tree_data(self):
        for group in self.add_group_service.get_all_groups():
            gid = self.tree.insert("", "end", text=group, tags=("group",), open=True)
            for chan in self.add_channel_service.get_channels_by_group(group):
                self.tree.insert(gid, "end", text=chan, tags=("channel",))

    def start_process(self):
        if not self.selected_items_list: return
        num_workers = int(self.params["Workers (Threads)"].get())
        for item in self.selected_items_list: self.task_queue.put(item)
        self.selected_items_list.clear()
        for child in self.queue_scroll.winfo_children():
            child.destroy()

        for i in range(num_workers):
            self.worker_count += 1
            card = DownloadWorkerCard(self.worker_container, self.worker_count)
            card.pack(fill=X, padx=5, pady=5)
            threading.Thread(target=self.worker_loop, args=(card,), daemon=True).start()

    def worker_loop(self, card):
        while True:
            if card.stop_event.is_set():
                break

            try:
                item_name = self.task_queue.get_nowait()
            except queue.Empty:
                break

            channel_info = self.add_channel_service.get_channel_details(item_name)
            if not channel_info:
                self.after(0, lambda c=card, n=item_name: c.update_log(f"Error: {n} not found in DB"))
                self.task_queue.task_done()
                continue

            videos = self.add_channel_service.get_videos_by_channel(item_name)
            if not videos:
                self.after(0, lambda c=card, n=item_name: c.update_log(f"No videos found in DB for {n}"))
                self.task_queue.task_done()
                continue

            cid = channel_info.get("channel_id", "Unknown_ID")
            handle = channel_info.get("handle", "Unknown_Handle")

            if handle and handle != "Unknown_Handle" and handle != cid:
                folder_name = f"{cid} ({handle})"
            else:
                folder_name = cid

            safe_handle = handle if handle.startswith('@') else f"@{handle}"

            self.after(0, lambda c=card, n=item_name, v=videos: c.update_ui_state(
                title=f"Downloading: {n}",
                status=f"Preparing download queue for {len(v)} videos..."
            ))

            ui_params = {
                "format": self.format_var.get(),
                "container": self.container_var.get(),
                "skip_downloaded": self.skip_downloaded_var.get(),
                "--sleep-interval": self.params["--sleep-interval"].get(),
                "--max-sleep-interval": self.params["--max-sleep-interval"].get(),
                "--sleep-requests": self.params["--sleep-requests"].get(),
                "--retries": self.params["--retries"].get(),
                "--fragment-retries": self.params["--fragment-retries"].get(),
                "use_cookies": self.cookie_var.get()
            }

            def log_cb(msg):
                self.after(0, lambda c=card, m=msg: c.update_log(m))

            def status_cb(msg, progress, total):
                val = (progress / total) * 100 if total > 0 else 0
                self.after(0, lambda c=card, m=msg, p=progress, t=total, v=val: c.update_ui_state(
                    status=m,
                    progress=f"Processed: {p}/{t}",
                    bar_val=v
                ))

            self.dlp_download_service.fetch(videos, channel_info.get("name"), ui_params, folder_name, safe_handle,
                                            log_cb, status_cb, card.stop_event)

            self.task_queue.task_done()

        final_msg = "Worker stopped." if card.stop_event.is_set() else "Worker idle. All assigned tasks complete."
        self.after(0, lambda c=card, s=final_msg: c.update_ui_state(
            status=s,
            bar_val=100
        ))