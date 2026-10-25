"""Main application window: header, summary cards, and the three tabs."""
import tkinter as tk
from tkinter import messagebox, ttk

from . import theme
from .analytics_tab import AnalyticsTab
from .goals_tab import GoalsTab
from .transactions_tab import TransactionsTab

ALL_TIME = "All time"


class MainWindow(tk.Tk):
    def __init__(self, service, username):
        super().__init__()
        self.service = service
        self.username = username
        self.logged_out = False

        self.title(f"Personal Finance & Budget Tracker - {username}")
        theme.apply_theme(self)
        theme.center(self, 1200, 740)
        self.minsize(1000, 640)

        self.period_var = tk.StringVar(value=ALL_TIME)
        self.value_vars = {k: tk.StringVar(value=theme.money(0))
                           for k in ("income", "expense", "balance")}
        self.caption_vars = {k: tk.StringVar() for k in ("income", "expense", "balance")}
        self.balance_label = None

        self._build_menu()
        self._build_header()
        self._build_cards()
        self._build_tabs()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.refresh_all()

    # ------------------------------------------------------------ layout
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load sample data", command=self.load_demo)
        file_menu.add_command(label="Export transactions to CSV...",
                              command=lambda: self.transactions_tab.export_csv())
        file_menu.add_separator()
        file_menu.add_command(label="Log out", command=self.logout)
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def _build_header(self):
        header = ttk.Frame(self, padding=(24, 18, 24, 0))
        header.pack(fill="x")
        left = ttk.Frame(header)
        left.pack(side="left")
        ttk.Label(left, text="💸 Finance Tracker", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text=f"Welcome back, {self.username} 👋",
                  style="MutedBg.TLabel").pack(anchor="w")

        ttk.Button(header, text="Log out", command=self.logout, cursor="hand2").pack(side="right")
        self.period_box = ttk.Combobox(header, textvariable=self.period_var,
                                       state="readonly", width=12)
        self.period_box.pack(side="right", padx=(6, 14))
        ttk.Label(header, text="Period:", style="MutedBg.TLabel").pack(side="right")
        self.period_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_all())

    def _build_cards(self):
        row = ttk.Frame(self, padding=(24, 16, 24, 14))
        row.pack(fill="x")
        specs = [("income", "💰", "Total Income", theme.INCOME),
                 ("expense", "💸", "Total Expenses", theme.EXPENSE),
                 ("balance", "🏦", "Balance", theme.ACCENT)]
        for i, (key, icon, title, color) in enumerate(specs):
            row.columnconfigure(i, weight=1, uniform="cards")
            label = self._make_card(row, i, icon, title, color, key)
            if key == "balance":
                self.balance_label = label

    def _make_card(self, parent, col, icon, title, color, key):
        card = tk.Frame(parent, bg=theme.CARD, highlightthickness=1,
                        highlightbackground=theme.BORDER)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 12, 0))
        tk.Frame(card, bg=color, height=4).pack(fill="x")          # colour strip
        body = tk.Frame(card, bg=theme.CARD)
        body.pack(fill="both", padx=18, pady=(12, 14))
        tk.Label(body, text=f"{icon}  {title}", bg=theme.CARD, fg=theme.MUTED,
                 font=theme.FONT).pack(anchor="w")
        value = tk.Label(body, textvariable=self.value_vars[key], bg=theme.CARD, fg=color,
                         font=theme.FONT_CARD)
        value.pack(anchor="w", pady=(2, 0))
        tk.Label(body, textvariable=self.caption_vars[key], bg=theme.CARD, fg=theme.MUTED,
                 font=theme.FONT_SMALL).pack(anchor="w")
        return value

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.transactions_tab = TransactionsTab(
            self.notebook, self.service, self.current_month, self.refresh_all)
        self.analytics_tab = AnalyticsTab(self.notebook, self.service, self.current_month)
        self.goals_tab = GoalsTab(self.notebook, self.service)

        self.notebook.add(self.transactions_tab, text="  💳  Transactions  ")
        self.notebook.add(self.analytics_tab, text="  📊  Analytics  ")
        self.notebook.add(self.goals_tab, text="  🎯  Savings Goals  ")
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.analytics_tab.refresh())

    # ----------------------------------------------------------- helpers
    def current_month(self):
        value = self.period_var.get()
        return None if value == ALL_TIME else value

    def refresh_all(self):
        options = [ALL_TIME] + self.service.period_options()
        self.period_box["values"] = options
        if self.period_var.get() not in options:
            self.period_var.set(ALL_TIME)

        s = self.service.summary(self.current_month())
        self.value_vars["income"].set(theme.money(s["income"]))
        self.value_vars["expense"].set(theme.money(s["expense"]))
        self.value_vars["balance"].set(theme.money(s["balance"]))
        self.balance_label.config(fg=theme.ACCENT if s["balance"] >= 0 else theme.EXPENSE)

        if s["income"] > 0:
            spent = s["expense"] / s["income"] * 100
            rate = s["balance"] / s["income"] * 100
            self.caption_vars["income"].set("Money in")
            self.caption_vars["expense"].set(f"{spent:.0f}% of income spent")
            self.caption_vars["balance"].set(f"Savings rate {rate:.0f}%")
        else:
            self.caption_vars["income"].set("Money in")
            self.caption_vars["expense"].set("Money out")
            self.caption_vars["balance"].set("Add income to see your savings rate")

        self.transactions_tab.refresh()
        self.analytics_tab.refresh()
        self.goals_tab.refresh()

    def load_demo(self):
        if messagebox.askyesno("Sample data", "Add ~3 months of sample transactions and goals?"):
            self.service.load_demo_data()
            self.refresh_all()

    def logout(self):
        self.logged_out = True
        self.destroy()
