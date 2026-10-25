"""Business-logic layer: validation, CSV export and demo data.
One FinanceService instance belongs to one logged-in user.
The GUI only talks to this class, never to SQL directly."""
import csv
import random
from datetime import date, datetime, timedelta

from .database import Database


class ValidationError(Exception):
    """Raised when user input is invalid; the message is safe to show in the UI."""


def parse_amount(value):
    try:
        amount = round(float(str(value).replace(",", "").strip()), 2)
    except ValueError:
        raise ValidationError("Amount must be a number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    return amount


def parse_date(value):
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format (e.g. 2026-10-25).")


class FinanceService:
    def __init__(self, db: Database, user_id: int):
        self.db = db
        self.uid = user_id

    # ------------------------------------------------------ transactions
    def _clean(self, tx_type, amount, category, description, tx_date):
        if tx_type not in ("Income", "Expense"):
            raise ValidationError("Type must be Income or Expense.")
        category = (category or "").strip().title()
        if not category:
            raise ValidationError("Please choose or type a category.")
        return (tx_type, parse_amount(amount), category,
                (description or "").strip(), parse_date(tx_date))

    def add_transaction(self, tx_type, amount, category, description, tx_date):
        return self.db.insert_transaction(
            self.uid, *self._clean(tx_type, amount, category, description, tx_date))

    def update_transaction(self, tx_id, tx_type, amount, category, description, tx_date):
        self.db.update_transaction(
            self.uid, tx_id, *self._clean(tx_type, amount, category, description, tx_date))

    def delete_transaction(self, tx_id):
        self.db.delete_transaction(self.uid, tx_id)

    def list_transactions(self, month=None, tx_type=None, search=None):
        return self.db.fetch_transactions(
            self.uid, month, tx_type, (search or "").strip() or None)

    def categories(self, tx_type):
        return self.db.get_categories(tx_type)

    # --------------------------------------------------------- analytics
    def summary(self, month=None):
        t = self.db.totals(self.uid, month)
        return {"income": t["Income"], "expense": t["Expense"],
                "balance": t["Income"] - t["Expense"]}

    def expense_breakdown(self, month=None):
        return self.db.category_breakdown(self.uid, "Expense", month)

    def monthly_totals(self, year):
        return self.db.monthly_totals(self.uid, year)

    def period_options(self):
        """Months that have data, plus the current month, newest first."""
        months = set(self.db.months_available(self.uid))
        months.add(date.today().strftime("%Y-%m"))
        return sorted(months, reverse=True)

    # ------------------------------------------------------------ goals
    def add_goal(self, name, target, deadline=""):
        name = (name or "").strip()
        if not name:
            raise ValidationError("Goal name is required.")
        deadline = (deadline or "").strip()
        if deadline:
            deadline = parse_date(deadline)
        self.db.insert_goal(self.uid, name, parse_amount(target), deadline)

    def list_goals(self):
        goals = self.db.fetch_goals(self.uid)
        for g in goals:
            g["progress"] = min(100.0, g["saved"] / g["target"] * 100)
        return goals

    def contribute_to_goal(self, goal_id, amount):
        self.db.add_to_goal(self.uid, goal_id, parse_amount(amount))

    def delete_goal(self, goal_id):
        self.db.delete_goal(self.uid, goal_id)

    # ----------------------------------------------------------- export
    def export_csv(self, path, rows):
        """Write the given transaction rows to a CSV file. Returns row count."""
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date", "Type", "Category", "Description", "Amount"])
            for r in rows:
                writer.writerow([r["id"], r["date"], r["type"], r["category"],
                                 r["description"], f"{r['amount']:.2f}"])
        return len(rows)

    # -------------------------------------------------------- demo data
    def load_demo_data(self):
        """Insert ~3 months of realistic sample data so charts look good."""
        rng = random.Random(42)
        today = date.today()
        samples = [
            ("Food", 40, 250), ("Transport", 20, 120), ("Entertainment", 100, 500),
            ("Education", 200, 900), ("Shopping", 300, 1500), ("Bills", 150, 400),
        ]
        for months_back in range(3):
            first = (today.replace(day=1) - timedelta(days=30 * months_back)).replace(day=1)
            self.add_transaction("Income", 8000, "Pocket Money", "Monthly allowance",
                                 first.isoformat())
            self.add_transaction("Income", rng.randint(1000, 3000), "Freelance",
                                 "Side project", first.replace(day=10).isoformat())
            for _ in range(12):
                cat, lo, hi = rng.choice(samples)
                self.add_transaction("Expense", rng.randint(lo, hi), cat, "",
                                     first.replace(day=rng.randint(2, 27)).isoformat())
        if not self.db.fetch_goals(self.uid):
            self.add_goal("New Laptop", 60000)
            self.add_goal("Trip with friends", 15000)
