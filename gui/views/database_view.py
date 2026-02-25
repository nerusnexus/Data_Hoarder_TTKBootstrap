import ttkbootstrap as ttk

class DatabaseView(ttk.Notebook):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.build()

    def build(self):
        treeview = ttk.Frame(self)
        manage = ttk.Frame(self)

        self.add(treeview, text="Treeview")
        self.add(manage, text="Manage")