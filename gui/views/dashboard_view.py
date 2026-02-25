import ttkbootstrap as ttk

class DashboardView(ttk.Notebook):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.build()

    def build(self):
        overview = ttk.Frame(self)
        details = ttk.Frame(self)

        self.add(overview, text="Overview")
        self.add(details, text="Details")

        ttk.Label(overview, text="Library Overview").pack(pady=20)
        ttk.Label(details, text="Library Details").pack(pady=20)