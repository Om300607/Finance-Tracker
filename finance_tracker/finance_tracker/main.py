"""Entry point: python main.py"""
from backend.auth import AuthService
from backend.database import Database
from backend.services import FinanceService
from frontend.login_window import LoginWindow
from frontend.main_window import MainWindow


def main():
    database = Database()
    auth = AuthService(database)
    while True:
        user = LoginWindow(auth).run()          # login / register screen
        if user is None:                        # window closed -> quit
            break
        service = FinanceService(database, user["id"])
        app = MainWindow(service, user["username"])
        app.mainloop()
        if not app.logged_out:                  # closed with X -> quit
            break                               # (Log out returns to login)
    database.close()


if __name__ == "__main__":
    main()
