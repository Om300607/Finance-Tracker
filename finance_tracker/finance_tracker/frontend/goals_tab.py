"""Savings goals tab: create goals, add savings, track progress."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from backend.services import ValidationError
from . import theme


class GoalsTab(ttk.Frame):
    def __init__(self, parent, service):
        super().__init__(parent, padding=12)
        self.service = service
        self.goals = []

        self.name_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.deadline_var = tk.StringVar()
        self.detail_var = tk.StringVar(value="Select a goal to see its progress.")
        self.progress_var = tk.DoubleVar(value=0)

        self._build_form()
        self._build_list()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="  New Savings Goal  ", padding=14)
        form.pack(side="left", fill="y", padx=(0, 12))
        rows = [("Goal name", self.name_var),
                (f"Target amount ({theme.CURRENCY})", self.target_var),
                ("Deadline (optional, YYYY-MM-DD)", self.deadline_var)]
        for i, (label, var) in enumerate(rows):
            ttk.Label(form, text=label, style="Card.TLabel").grid(row=i * 2, column=0, sticky="w")
            ttk.Entry(form, textvariable=var, width=28).grid(
                row=i * 2 + 1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(form, text="Add Goal", style="Accent.TButton",
                   command=self.add_goal).grid(row=6, column=0, sticky="ew", pady=(10, 0))

    def _build_list(self):
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        bar = ttk.Frame(right)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Add Savings", style="Accent.TButton",
                   command=self.add_savings).pack(side="left")
        ttk.Button(bar, text="Delete Goal", style="Danger.TButton",
                   command=self.delete_goal).pack(side="left", padx=8)

        cols = ("name", "target", "saved", "progress", "deadline")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse", height=10)
        widths = {"name": 200, "target": 110, "saved": 110, "progress": 90, "deadline": 100}
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=widths[c], anchor="w" if c in ("name", "deadline") else "e")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        detail = ttk.Frame(right, style="Card.TFrame", padding=12)
        detail.pack(fill="x", pady=(10, 0))
        ttk.Label(detail, textvariable=self.detail_var, style="Heading.TLabel").pack(anchor="w")
        ttk.Progressbar(detail, variable=self.progress_var, maximum=100,
                        style="Goal.Horizontal.TProgressbar").pack(fill="x", pady=(8, 0))

    def _selected_goal(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Goals", "Select a goal in the table first.")
            return None
        gid = int(sel[0])
        return next((g for g in self.goals if g["id"] == gid), None)

    def add_goal(self):
        try:
            self.service.add_goal(self.name_var.get(), self.target_var.get(), self.deadline_var.get())
        except ValidationError as e:
            messagebox.showwarning("Invalid input", str(e))
            return
        for var in (self.name_var, self.target_var, self.deadline_var):
            var.set("")
        self.refresh()

    def add_savings(self):
        goal = self._selected_goal()
        if goal is None:
            return
        value = simpledialog.askstring(
            "Add savings", f"How much to add to '{goal['name']}' ({theme.CURRENCY})?", parent=self)
        if value is None:
            return
        try:
            self.service.contribute_to_goal(goal["id"], value)
        except ValidationError as e:
            messagebox.showwarning("Invalid input", str(e))
            return
        self.refresh(select_id=goal["id"])

    def delete_goal(self):
        goal = self._selected_goal()
        if goal and messagebox.askyesno("Delete", f"Delete goal '{goal['name']}'?"):
            self.service.delete_goal(goal["id"])
            self.refresh()

    def _on_select(self, _event):
        sel = self.tree.selection()
        goal = next((g for g in self.goals if str(g["id"]) == sel[0]), None) if sel else None
        if goal is None:
            self.detail_var.set("Select a goal to see its progress.")
            self.progress_var.set(0)
            return
        remaining = max(goal["target"] - goal["saved"], 0)
        self.detail_var.set(
            f"{goal['name']}: {theme.money(goal['saved'])} of {theme.money(goal['target'])} "
            f"saved ({goal['progress']:.0f}%) - {theme.money(remaining)} to go")
        self.progress_var.set(goal["progress"])

    def refresh(self, select_id=None):
        self.goals = self.service.list_goals()
        self.tree.delete(*self.tree.get_children())
        for g in self.goals:
            self.tree.insert("", "end", iid=str(g["id"]),
                             values=(g["name"], theme.money(g["target"]), theme.money(g["saved"]),
                                     f"{g['progress']:.0f}%", g["deadline"] or "-"))
        if select_id is not None and self.tree.exists(str(select_id)):
            self.tree.selection_set(str(select_id))
        else:
            self._on_select(None)
