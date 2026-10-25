"""Analytics tab: dark-themed matplotlib charts embedded in the Tkinter window."""
import calendar
from datetime import date
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from . import theme


def _short(value, _pos=None):
    return f"{value / 1000:g}k" if abs(value) >= 1000 else f"{value:g}"


class AnalyticsTab(ttk.Frame):
    def __init__(self, parent, service, get_period):
        super().__init__(parent, padding=12)
        self.service = service
        self.get_period = get_period

        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor=theme.BG)
        grid = self.figure.add_gridspec(1, 2, width_ratios=[1, 1.3])
        self.pie_ax = self.figure.add_subplot(grid[0, 0])
        self.bar_ax = self.figure.add_subplot(grid[0, 1])
        self.figure.subplots_adjust(left=0.03, right=0.98, top=0.9, bottom=0.2, wspace=0.22)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=theme.BG, highlightthickness=0)
        widget.pack(fill="both", expand=True)

    def refresh(self):
        month = self.get_period()
        self._draw_donut(month)
        self._draw_bars(month)
        self.canvas.draw_idle()

    def _draw_donut(self, month):
        ax = self.pie_ax
        ax.clear()
        ax.set_facecolor(theme.BG)
        ax.set_title("Spending by category · " + (month or "all time"), fontsize=11,
                     fontweight="bold", color=theme.TEXT, pad=12)
        data = self.service.expense_breakdown(month)
        if not data:
            ax.text(0.5, 0.5, "No expenses yet\nAdd one in the Transactions tab",
                    ha="center", va="center", color=theme.MUTED, fontsize=10,
                    transform=ax.transAxes)
            ax.axis("off")
            return
        labels = [c for c, _ in data]
        values = [v for _, v in data]
        colors = [theme.CHART_COLORS[i % len(theme.CHART_COLORS)] for i in range(len(values))]
        wedges, _texts, autotexts = ax.pie(
            values, colors=colors, startangle=90, counterclock=False,
            autopct=lambda p: f"{p:.0f}%" if p >= 6 else "", pctdistance=0.8,
            wedgeprops={"width": 0.42, "edgecolor": theme.BG, "linewidth": 2})
        for t in autotexts:
            t.set_color("white")
            t.set_fontsize(8)
            t.set_fontweight("bold")
        total = sum(values)
        ax.text(0, 0.06, f"{theme.CURRENCY}{total:,.0f}", ha="center", va="center",
                color=theme.TEXT, fontsize=14, fontweight="bold")
        ax.text(0, -0.14, "spent", ha="center", va="center", color=theme.MUTED, fontsize=9)
        ax.legend(wedges, labels, loc="upper center", bbox_to_anchor=(0.5, 0.02),
                  ncol=3, frameon=False, fontsize=8, labelcolor=theme.TEXT,
                  handlelength=1, columnspacing=1.2)
        ax.axis("equal")

    def _draw_bars(self, month):
        ax = self.bar_ax
        ax.clear()
        year = int(month[:4]) if month else date.today().year
        totals = self.service.monthly_totals(year)
        months = list(range(1, 13))
        income = [totals[m]["Income"] for m in months]
        expense = [totals[m]["Expense"] for m in months]
        width = 0.38
        ax.set_facecolor(theme.CARD)
        ax.bar([m - width / 2 for m in months], income, width, label="Income",
               color=theme.INCOME)
        ax.bar([m + width / 2 for m in months], expense, width, label="Expense",
               color=theme.EXPENSE)
        ax.set_xticks(months)
        ax.set_xticklabels([calendar.month_abbr[m] for m in months], fontsize=8)
        ax.tick_params(colors=theme.MUTED, length=0)
        ax.yaxis.set_major_formatter(FuncFormatter(_short))
        ax.set_title(f"Income vs expense · {year}", fontsize=11, fontweight="bold",
                     color=theme.TEXT, pad=12)
        ax.grid(axis="y", color=theme.BORDER, alpha=0.5, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(theme.BORDER)
        ax.legend(frameon=False, labelcolor=theme.TEXT, fontsize=9, loc="upper right")
