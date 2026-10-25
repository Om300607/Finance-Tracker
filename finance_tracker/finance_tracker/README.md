# Personal Finance & Budget Tracker

A desktop app for students to track income/expenses, set savings goals and
visualise spending. Built with Python, Tkinter, SQLite and matplotlib.

## Run
    pip install -r requirements.txt
    python main.py

Tkinter ships with Python (on Linux: `sudo apt install python3-tk`).
On first launch click **Create an account**, then use
**File > Load sample data** to see the charts with demo data.

## Structure
    main.py                       entry point (login -> app -> logout loop)
    backend/database.py           SQLite schema + all SQL queries (data layer)
    backend/auth.py               register / login, salted PBKDF2 password hashing
    backend/services.py           validation, business rules, CSV export (logic layer)
    frontend/theme.py             dark theme: colours, fonts, ttk styles
    frontend/login_window.py      login / sign-up screen
    frontend/main_window.py       header, summary cards, period filter, tabs
    frontend/transactions_tab.py  add/edit/delete/search/filter/export
    frontend/analytics_tab.py     embedded matplotlib donut + bar charts
    frontend/goals_tab.py         savings goals with progress bar
    data/finance.db               created automatically on first run

## Features
- Multi-user login: every account sees only its own data
- Passwords are salted and hashed (PBKDF2-SHA256), never stored in plain text
- CRUD for income/expense transactions (SQLite, parameterised queries)
- Categories stored in their own table; type a new one to create it
- Donut chart of spending by category + yearly income-vs-expense bars
- Month filter, type filter and text search
- Export the currently filtered transactions to CSV (opens in Excel)
- Savings goals with progress tracking
