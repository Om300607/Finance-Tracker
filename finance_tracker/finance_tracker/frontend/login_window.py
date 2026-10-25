"""Login / registration window shown before the main app."""
import tkinter as tk
from tkinter import ttk

from backend.auth import AuthError
from . import theme


class LoginWindow(tk.Tk):
    W, H, SIDE = 860, 580, 380

    def __init__(self, auth):
        super().__init__()
        self.auth = auth
        self.user = None
        self.mode = "login"

        self.title("Finance Tracker - Sign in")
        theme.apply_theme(self)
        theme.center(self, self.W, self.H)
        self.resizable(False, False)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        self.show_var = tk.BooleanVar(value=False)
        self.error_var = tk.StringVar()
        self.heading_var = tk.StringVar()
        self.sub_var = tk.StringVar()
        self.submit_var = tk.StringVar()
        self.switch_text_var = tk.StringVar()
        self.switch_btn_var = tk.StringVar()

        self._build_brand()
        self._build_form()
        self.set_mode("login")
        self.bind("<Return>", lambda _e: self.submit())
        self.username_entry.focus_set()

    # ----------------------------------------------------------- layout
    def _build_brand(self):
        canvas = tk.Canvas(self, width=self.SIDE, height=self.H, highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="y")
        for y in range(self.H):  # vertical gradient
            canvas.create_line(0, y, self.SIDE, y,
                               fill=theme.blend("#4338ca", "#a21caf", y / self.H))
        cx = self.SIDE // 2
        canvas.create_text(cx, 120, text="💸", font=("Segoe UI Emoji", 52), fill="white")
        canvas.create_text(cx, 210, text="Finance Tracker", fill="white",
                           font=("Segoe UI", 26, "bold"))
        canvas.create_text(cx, 250, text="Take control of your money.", fill="#e0e7ff",
                           font=("Segoe UI", 12))
        features = ["📊  Visual spending analytics", "🎯  Savings goals & progress",
                    "🔒  Private, local & secure", "📁  One-click CSV export"]
        for i, text in enumerate(features):
            canvas.create_text(70, 330 + i * 36, text=text, anchor="w", fill="white",
                               font=("Segoe UI", 11))
        canvas.create_text(cx, self.H - 28, text="Built with Python • Tkinter • SQLite",
                           fill="#c7d2fe", font=("Segoe UI", 9))

    def _build_form(self):
        side = tk.Frame(self, bg=theme.CARD)
        side.pack(side="right", fill="both", expand=True)
        form = ttk.Frame(side, style="Card.TFrame")
        form.place(relx=0.5, rely=0.5, anchor="center", width=360)
        form.columnconfigure(0, weight=1)

        ttk.Label(form, textvariable=self.heading_var, style="Card.TLabel",
                  font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(form, textvariable=self.sub_var, style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 18))

        ttk.Label(form, text="Username", style="Card.TLabel").grid(row=2, column=0, sticky="w")
        self.username_entry = ttk.Entry(form, textvariable=self.username_var)
        self.username_entry.grid(row=3, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(form, text="Password", style="Card.TLabel").grid(row=4, column=0, sticky="w")
        self.password_entry = ttk.Entry(form, textvariable=self.password_var, show="•")
        self.password_entry.grid(row=5, column=0, sticky="ew", pady=(2, 10))

        self.confirm_label = ttk.Label(form, text="Confirm password", style="Card.TLabel")
        self.confirm_label.grid(row=6, column=0, sticky="w")
        self.confirm_entry = ttk.Entry(form, textvariable=self.confirm_var, show="•")
        self.confirm_entry.grid(row=7, column=0, sticky="ew", pady=(2, 10))

        ttk.Checkbutton(form, text="Show password", variable=self.show_var,
                        style="Card.TCheckbutton", command=self._toggle_show).grid(
            row=8, column=0, sticky="w")

        tk.Label(form, textvariable=self.error_var, bg=theme.CARD, fg=theme.EXPENSE,
                 font=theme.FONT_SMALL, wraplength=340, justify="left", anchor="w").grid(
            row=9, column=0, sticky="ew", pady=(8, 0))

        ttk.Button(form, textvariable=self.submit_var, style="Accent.TButton",
                   command=self.submit, cursor="hand2").grid(
            row=10, column=0, sticky="ew", pady=(10, 14))

        switch = ttk.Frame(form, style="Card.TFrame")
        switch.grid(row=11, column=0)
        ttk.Label(switch, textvariable=self.switch_text_var, style="Muted.TLabel").pack(side="left")
        ttk.Button(switch, textvariable=self.switch_btn_var, style="Link.TButton",
                   command=self.toggle_mode, cursor="hand2").pack(side="left", padx=(6, 0))

    # ----------------------------------------------------------- logic
    def _toggle_show(self):
        char = "" if self.show_var.get() else "•"
        self.password_entry.config(show=char)
        self.confirm_entry.config(show=char)

    def set_mode(self, mode):
        self.mode = mode
        self.error_var.set("")
        self.password_var.set("")
        self.confirm_var.set("")
        if mode == "login":
            self.title("Finance Tracker - Sign in")
            self.heading_var.set("Welcome back")
            self.sub_var.set("Sign in to open your dashboard")
            self.submit_var.set("Sign In")
            self.switch_text_var.set("New here?")
            self.switch_btn_var.set("Create an account")
            self.confirm_label.grid_remove()
            self.confirm_entry.grid_remove()
        else:
            self.title("Finance Tracker - Create account")
            self.heading_var.set("Create account")
            self.sub_var.set("Start tracking your money in seconds")
            self.submit_var.set("Create Account")
            self.switch_text_var.set("Already have an account?")
            self.switch_btn_var.set("Sign in")
            self.confirm_label.grid()
            self.confirm_entry.grid()

    def toggle_mode(self):
        self.set_mode("register" if self.mode == "login" else "login")

    def submit(self):
        try:
            if self.mode == "login":
                user = self.auth.login(self.username_var.get(), self.password_var.get())
            else:
                user = self.auth.register(self.username_var.get(), self.password_var.get(),
                                          self.confirm_var.get())
        except AuthError as e:
            self.error_var.set(str(e))
            return
        self.user = user
        self.destroy()

    def run(self):
        """Show the window; returns the logged-in user dict, or None if closed."""
        self.mainloop()
        return self.user
