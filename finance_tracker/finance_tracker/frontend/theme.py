"""Shared colours, fonts and ttk styling (dark modern theme)."""
from tkinter import ttk

CURRENCY = "₹"

BG = "#0b1220"
SURFACE = "#0f172a"
CARD = "#162033"
CARD_ALT = "#1c2940"
BORDER = "#2a3a57"
PRIMARY = "#6366f1"
PRIMARY_HOVER = "#818cf8"
ACCENT = "#22d3ee"
INCOME = "#34d399"
EXPENSE = "#f87171"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
SELECT = "#312e81"

CHART_COLORS = ["#6366f1", "#22d3ee", "#34d399", "#fbbf24", "#f472b6",
                "#a78bfa", "#fb923c", "#60a5fa", "#f87171", "#2dd4bf"]

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_CARD = ("Segoe UI", 20, "bold")


def money(value):
    return f"{CURRENCY}{value:,.2f}"


def blend(c1, c2, t):
    """Linear blend between two #rrggbb colours (t from 0 to 1)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def center(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() - width) // 2
    y = max((win.winfo_screenheight() - height) // 2 - 20, 0)
    win.geometry(f"{width}x{height}+{x}+{y}")


def apply_theme(root):
    root.configure(bg=BG)
    # dark dropdown lists for comboboxes
    root.option_add("*TCombobox*Listbox.background", CARD_ALT)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", PRIMARY)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")
    root.option_add("*TCombobox*Listbox.font", FONT)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, fieldbackground=CARD_ALT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    troughcolor=SURFACE, focuscolor=BG, font=FONT)

    # frames & labels
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Muted.TLabel", background=CARD, foreground=MUTED)
    style.configure("MutedBg.TLabel", background=BG, foreground=MUTED)
    style.configure("Title.TLabel", font=FONT_TITLE, foreground=TEXT)
    style.configure("Heading.TLabel", font=FONT_BOLD, background=CARD, foreground=TEXT)
    style.configure("TLabelframe", background=CARD, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=CARD, font=FONT_BOLD, foreground=ACCENT)

    # inputs
    style.configure("TEntry", fieldbackground=CARD_ALT, foreground=TEXT, insertcolor=TEXT,
                    padding=7, bordercolor=BORDER, lightcolor=CARD_ALT, darkcolor=CARD_ALT)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)], darkcolor=[("focus", PRIMARY)])
    style.configure("TCombobox", fieldbackground=CARD_ALT, background=CARD_ALT,
                    foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER,
                    lightcolor=CARD_ALT, darkcolor=CARD_ALT, padding=6,
                    selectbackground=CARD_ALT, selectforeground=TEXT)
    style.map("TCombobox",
              fieldbackground=[("readonly", CARD_ALT)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", CARD_ALT)],
              selectforeground=[("readonly", TEXT)],
              bordercolor=[("focus", PRIMARY)],
              arrowcolor=[("active", ACCENT)])
    style.configure("TRadiobutton", background=CARD, foreground=TEXT)
    style.map("TRadiobutton", background=[("active", CARD)],
              indicatorcolor=[("selected", PRIMARY), ("!selected", CARD_ALT)])
    style.configure("Card.TCheckbutton", background=CARD, foreground=MUTED)
    style.map("Card.TCheckbutton", background=[("active", CARD)],
              indicatorcolor=[("selected", PRIMARY), ("!selected", CARD_ALT)])

    # buttons
    style.configure("TButton", background=CARD_ALT, foreground=TEXT, padding=8,
                    bordercolor=BORDER, font=FONT)
    style.map("TButton", background=[("active", "#243352")])
    style.configure("Accent.TButton", background=PRIMARY, foreground="white",
                    font=FONT_BOLD, padding=9, bordercolor=PRIMARY)
    style.map("Accent.TButton", background=[("active", PRIMARY_HOVER)],
              bordercolor=[("active", PRIMARY_HOVER)])
    style.configure("Danger.TButton", background="#dc2626", foreground="white",
                    font=FONT_BOLD, padding=9, bordercolor="#dc2626")
    style.map("Danger.TButton", background=[("active", "#ef4444")],
              bordercolor=[("active", "#ef4444")])
    style.configure("Link.TButton", background=CARD, foreground=ACCENT, borderwidth=0,
                    padding=2, font=FONT_BOLD)
    style.map("Link.TButton", background=[("active", CARD)],
              foreground=[("active", PRIMARY_HOVER)])

    # tabs
    style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure("TNotebook.Tab", padding=(22, 11), font=FONT_BOLD,
                    background=SURFACE, foreground=MUTED, borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", CARD), ("active", CARD_ALT)],
              foreground=[("selected", ACCENT), ("active", TEXT)])

    # tables
    style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=32, borderwidth=0, font=FONT)
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview.Heading", background=CARD_ALT, foreground=ACCENT,
                    font=FONT_BOLD, padding=9, relief="flat", borderwidth=0)
    style.map("Treeview", background=[("selected", SELECT)],
              foreground=[("selected", "white")])
    style.map("Treeview.Heading", background=[("active", BORDER)])

    style.configure("Vertical.TScrollbar", background=CARD_ALT, troughcolor=SURFACE,
                    arrowcolor=MUTED, bordercolor=SURFACE, lightcolor=CARD_ALT,
                    darkcolor=CARD_ALT)
    style.map("Vertical.TScrollbar", background=[("active", BORDER)])

    style.configure("Goal.Horizontal.TProgressbar", troughcolor=CARD_ALT,
                    background=INCOME, lightcolor=INCOME, darkcolor=INCOME,
                    bordercolor=CARD, thickness=16)
