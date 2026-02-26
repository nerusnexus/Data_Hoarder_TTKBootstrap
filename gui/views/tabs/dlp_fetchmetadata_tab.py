import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame


class MetadataWorkerCard(ttk.Frame):
    """A dynamic card that shows the progress and logs of a single yt-dlp worker."""

    def __init__(self, parent, worker_id):
        super().__init__(parent, bootstyle="secondary", padding=10)
        self.pack(fill=X, pady=5, padx=10)

        # Left Side: Stats & Progress
        self.stats_frame = ttk.Frame(self, width=300, bootstyle="secondary")
        self.stats_frame.pack(side=LEFT, fill=Y)
        self.stats_frame.pack_propagate(False)

        self.title_label = ttk.Label(self.stats_frame, text=f"Worker #{worker_id}: Idle", font=("Segoe UI", 10, "bold"))
        self.title_label.pack(anchor=W)

        self.progress_text = ttk.Label(self.stats_frame, text="Processed: 0/0")
        self.progress_text.pack(anchor=W, pady=5)

        self.progress_bar = ttk.Progressbar(self.stats_frame, bootstyle="success", mode="determinate")
        self.progress_bar.pack(fill=X, pady=5)

        self.status_label = ttk.Label(self.stats_frame, text="Waiting...", font=("Segoe UI", 8), wraplength=280)
        self.status_label.pack(anchor=W)

        # Right Side: Verbose Log
        self.log_text = ttk.Text(self, height=6, font=("Consolas", 8), state=DISABLED)
        self.log_text.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

    def update_log(self, message):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)


class DlpFetchMetadataTab(ttk.Frame):
    def __init__(self, parent, add_group_service, add_channel_service):
        super().__init__(parent)
        self.add_group_service = add_group_service
        self.add_channel_service = add_channel_service

        self.main_scroll = ScrolledFrame(self, autohide=True)
        self.main_scroll.pack(fill=BOTH, expand=True)

        self.worker_container = None
        self.tree = None
        self.params = {}
        self.combos = {}  # Store combo widgets to update them via modes

        self.build_ui()

    def build_ui(self):
        top_frame = ttk.Frame(self.main_scroll)
        top_frame.pack(fill=X, padx=10, pady=10)

        # --- LEFT COLUMN: Channel Treeview (Fixed Width) ---
        tree_outer = ttk.Frame(top_frame, width=300)
        tree_outer.pack(side=LEFT, fill=Y, padx=(0, 10))
        tree_outer.pack_propagate(False)

        tree_frame = ttk.Labelframe(tree_outer, text="Select Channels", padding=10)
        tree_frame.pack(fill=BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL)
        tree_scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(
            tree_frame,
            selectmode="extended",
            show="tree",
            yscrollcommand=tree_scroll.set
        )
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.load_tree_data()

        # --- RIGHT COLUMN: Configuration Parameters ---
        config_outer = ttk.Frame(top_frame)
        config_outer.pack(side=RIGHT, fill=BOTH, expand=True)

        config_frame = ttk.Labelframe(config_outer, text="yt-dlp Parameters", padding=10)
        config_frame.pack(fill=BOTH, expand=True)

        # Mode Selection at the top of parameters
        mode_frame = ttk.Frame(config_frame)
        mode_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(mode_frame, text="Speed Preset:", font=("Segoe UI", 9, "bold")).pack(side=LEFT)
        self.mode_var = ttk.StringVar(value="Default")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=["Slow", "Default", "Fast"],
                                  state="readonly", width=10)
        mode_combo.pack(side=LEFT, padx=10)
        mode_combo.bind("<<ComboboxSelected>>", self.apply_speed_preset)

        params_container = ttk.Frame(config_frame)
        params_container.pack(fill=BOTH, expand=True)

        # 1. Mandatory/Optional Flags (Left)
        left_params = ttk.Frame(params_container)
        left_params.pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        ttk.Label(left_params, text="Locked/Hardcoded:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(0, 5))
        for flag in ["--skip-download", "--write-info-json", "--write-playlist-metafiles"]:
            var = ttk.BooleanVar(value=True)
            ttk.Checkbutton(left_params, text=flag, variable=var, state=DISABLED).pack(anchor=W, padx=5)
            self.params[flag] = var

        ttk.Label(left_params, text="Options:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(10, 5))
        for flag in ["--write-description", "--write-thumbnail"]:
            var = ttk.BooleanVar(value=True)
            ttk.Checkbutton(left_params, text=flag, variable=var).pack(anchor=W, padx=5)
            self.params[flag] = var

        self.cookie_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(left_params, text="Use Firefox Cookies", variable=self.cookie_var).pack(anchor=W, padx=5,
                                                                                                pady=(5, 0))

        # 2. Numeric Parameters (Right)
        right_params = ttk.Frame(params_container)
        right_params.pack(side=RIGHT, fill=BOTH, expand=True, padx=5)

        # Config: (Label, Default, Values_List)
        inputs = [
            ("Workers (Threads)", "1", [str(i) for i in range(1, 17)]),
            ("-N (Concurrent Frags)", "4", [str(i) for i in range(1, 33)]),
            ("-r (Rate Limit)", "8M", ["1M", "2M", "4M", "8M", "16M", "32M", "No Limit"]),
            ("--sleep-requests", "1", [str(i) for i in range(0, 11)]),
            ("--sleep-interval", "10", [str(i) for i in range(0, 61, 5)]),
            ("--max-sleep-interval", "30", [str(i) for i in range(0, 121, 10)]),
            ("--sleep-subtitles", "5", [str(i) for i in range(0, 31)]),
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

        ttk.Button(config_outer, text="START FETCHING", bootstyle="success", command=self.start_process).pack(fill=X,
                                                                                                              pady=10)

        # --- BOTTOM SECTION: Worker Cards ---
        self.worker_container = ttk.Labelframe(self.main_scroll, text="Active Workers")
        self.worker_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def apply_speed_preset(self, _event):
        mode = self.mode_var.get()
        # Define settings for [Slow, Default, Fast]
        # Format: (sleep_req, sleep_int, max_sleep, N, rate, sleep_sub)
        presets = {
            "Slow": ("2", "20", "60", "2", "4M", "10"),
            "Default": ("1", "10", "30", "4", "8M", "5"),
            "Fast": ("0", "5", "15", "8", "16M", "2")
        }
        vals = presets[mode]
        self.params["--sleep-requests"].set(vals[0])
        self.params["--sleep-interval"].set(vals[1])
        self.params["--max-sleep-interval"].set(vals[2])
        self.params["-N (Concurrent Frags)"].set(vals[3])
        self.params["-r (Rate Limit)"].set(vals[4])
        self.params["--sleep-subtitles"].set(vals[5])

    def load_tree_data(self):
        groups = self.add_group_service.get_all_groups()
        for group in groups:
            gid = self.tree.insert("", "end", text=group, tags=("group",), open=True)
            channels = self.add_channel_service.get_channels_by_group(group)
            for chan in channels:
                self.tree.insert(gid, "end", text=chan, tags=("channel",))

    def start_process(self):
        for child in self.worker_container.winfo_children():
            child.destroy()
        try:
            num_workers = int(self.params["Workers (Threads)"].get())
        except ValueError:
            num_workers = 1
        for i in range(num_workers):
            MetadataWorkerCard(self.worker_container, i + 1)