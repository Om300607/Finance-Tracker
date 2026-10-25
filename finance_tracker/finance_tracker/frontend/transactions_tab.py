"""Transactions tab: add / edit / delete / search / filter / export CSV."""
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from backend.services import ValidationError
from . import theme


class TransactionsTab(ttk.Frame):
    def __init__(self, parent, service, get_period, on_change):
        super().__init__(parent, padding=12)
        self.service = service
        self.get_period = get_period      # callable -> "YYYY-MM" or None
        self.on_change = on_change        # callable: refresh the whole app
        self.selected_id = None
        self.rows = []

        self.type_var = tk.StringVar(value="Expense")
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.desc_var = tk.StringVar()
        self.filter_type = tk.StringVar(value="All")
        self.search_var = tk.StringVar()

        self._build_form()
        self._build_list()
        self._update_category_choices()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        self.filter_type.trace_add("write", lambda *_: self.refresh())

    # ------------------------------------------------------------ layout
    def _build_form(self):
        form = ttk.LabelFrame(self, text="  Transaction  ", padding=14)
        form.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(form, text="Type", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        row = ttk.Frame(form, style="Card.TFrame")
        row.grid(row=1, column=0, sticky="w", pady=(0, 8))
        for t in ("Expense", "Income"):
            ttk.Radiobutton(row, text=t, value=t, variable=self.type_var,
                            command=self._update_category_choices).pack(side="left", padx=(0, 10))

        self._field(form, 2, "Amount", ttk.Entry(form, textvariable=self.amount_var, width=28))
        self.category_box = ttk.Combobox(form, textvariable=self.category_var, width=26)
        self._field(form, 4, "Category (type to add a new one)", self.category_box)
        self._field(form, 6, "Date (YYYY-MM-DD)", ttk.Entry(form, textvariable=self.date_var, width=28))
        self._field(form, 8, "Description", ttk.Entry(form, textvariable=self.desc_var, width=28))

        self.save_btn = ttk.Button(form, text="Add Transaction", style="Accent.TButton",
                                   command=self.save)
        self.save_btn.grid(row=10, column=0, sticky="ew", pady=(14, 4))
        ttk.Button(form, text="Clear Form", command=self.clear_form).grid(
            row=11, column=0, sticky="ew")

    def _field(self, parent, row, label, widget):
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w")
        widget.grid(row=row + 1, column=0, sticky="ew", pady=(0, 8))

    def _build_list(self):
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        bar = ttk.Frame(right)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Show:").pack(side="left")
        ttk.Combobox(bar, textvariable=self.filter_type, width=9, state="readonly",
                     values=["All", "Income", "Expense"]).pack(side="left", padx=(6, 14))
        ttk.Label(bar, text="Search:").pack(side="left")
        ttk.Entry(bar, textvariable=self.search_var, width=24).pack(side="left", padx=6)
        ttk.Button(bar, text="Export CSV", style="Accent.TButton",
                   command=self.export_csv).pack(side="right")
        ttk.Button(bar, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected).pack(side="right", padx=8)

        cols = ("date", "type", "category", "description", "amount")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        widths = {"date": 100, "type": 80, "category": 130, "description": 240, "amount": 110}
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=widths[c], anchor="e" if c == "amount" else "w")
        self.tree.tag_configure("Income", foreground=theme.INCOME)
        self.tree.tag_configure("Expense", foreground=theme.EXPENSE)
        scroll = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ----------------------------------------------------------- actions
    def _update_category_choices(self):
        choices = self.service.categories(self.type_var.get())
        self.category_box["values"] = choices
        if self.category_var.get() not in choices and self.selected_id is None:
            self.category_var.set(choices[0] if choices else "")

    def save(self):
        args = (self.type_var.get(), self.amount_var.get(), self.category_var.get(),
                self.desc_var.get(), self.date_var.get())
        try:
            if self.selected_id is None:
                self.service.add_transaction(*args)
            else:
                self.service.update_transaction(self.selected_id, *args)
        except ValidationError as e:
            messagebox.showwarning("Invalid input", str(e))
            return
        self.clear_form()
        self.on_change()

    def clear_form(self):
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())
        self.amount_var.set("")
        self.desc_var.set("")
        self.date_var.set(date.today().isoformat())
        self.save_btn.config(text="Add Transaction")
        self._update_category_choices()

    def delete_selected(self):
        if self.selected_id is None:
            messagebox.showinfo("Delete", "Select a transaction in the table first.")
            return
        if messagebox.askyesno("Delete", "Delete this transaction permanently?"):
            self.service.delete_transaction(self.selected_id)
            self.clear_form()
            self.on_change()

    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        tx_id = int(sel[0])
        row = next((r for r in self.rows if r["id"] == tx_id), None)
        if row is None:
            return
        self.selected_id = tx_id
        self.type_var.set(row["type"])
        self.category_box["values"] = self.service.categories(row["type"])
        self.category_var.set(row["category"])
        self.amount_var.set(f"{row['amount']:.2f}")
        self.date_var.set(row["date"])
        self.desc_var.set(row["description"])
        self.save_btn.config(text="Update Transaction")

    def export_csv(self):
        if not self.rows:
            messagebox.showinfo("Export", "There are no transactions to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"transactions_{date.today().isoformat()}.csv")
        if not path:
            return
        try:
            count = self.service.export_csv(path, self.rows)
        except OSError as e:
            messagebox.showerror("Export failed", str(e))
            return
        messagebox.showinfo("Export complete", f"Saved {count} transactions to:\n{path}")

    # ----------------------------------------------------------- refresh
    def refresh(self):
        tx_type = self.filter_type.get()
        self.rows = self.service.list_transactions(
            month=self.get_period(),
            tx_type=None if tx_type == "All" else tx_type,
            search=self.search_var.get())
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:
            sign = "+" if r["type"] == "Income" else "-"
            self.tree.insert("", "end", iid=str(r["id"]), tags=(r["type"],),
                             values=(r["date"], r["type"], r["category"],
                                     r["description"], f"{sign}{theme.money(r['amount'])}"))
        self._update_category_choices()
