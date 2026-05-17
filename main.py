# main.py
# ============================================
# Run this file to start the app:
#   python main.py
# ============================================

import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import APP_NAME, CHECKPOSTS
from database.local_db import test_connection


class LoginWindow:
    """
    Simple login screen shown before the main app.
    Officer enters their name and selects their checkpost.
    """
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} — Login")
        self.root.geometry("420x320")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        # Center it
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - 210
        y = (self.root.winfo_screenheight() // 2) - 160
        self.root.geometry(f"420x320+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # Logo area
        tk.Label(
            self.root,
            text="🇳🇵",
            font=("Helvetica", 36),
            bg="#1a1a2e"
        ).pack(pady=(25, 5))

        tk.Label(
            self.root,
            text="NEPAL TOURIST TICKETING",
            font=("Helvetica", 13, "bold"),
            bg="#1a1a2e", fg="white"
        ).pack()

        tk.Label(
            self.root,
            text="Officer Login",
            font=("Helvetica", 10),
            bg="#1a1a2e", fg="#AEB6BF"
        ).pack(pady=(2, 20))

        # Form
        form = tk.Frame(self.root, bg="#1a1a2e")
        form.pack()

        # Officer name
        tk.Label(form, text="Officer Name:", font=("Helvetica", 10),
                 bg="#1a1a2e", fg="#AEB6BF").grid(row=0, column=0, sticky="e", padx=8, pady=6)

        self.name_entry = tk.Entry(form, font=("Helvetica", 10),
                                   width=22, relief="solid")
        self.name_entry.grid(row=0, column=1, ipady=4)
        self.name_entry.focus()

        # Checkpost
        tk.Label(form, text="Checkpost:", font=("Helvetica", 10),
                 bg="#1a1a2e", fg="#AEB6BF").grid(row=1, column=0, sticky="e", padx=8, pady=6)

        self.cp_var = tk.StringVar(value=CHECKPOSTS[0])
        ttk.Combobox(
            form,
            textvariable=self.cp_var,
            values=CHECKPOSTS,
            state="readonly",
            font=("Helvetica", 10),
            width=20
        ).grid(row=1, column=1, ipady=4)

        # Login button
        tk.Button(
            self.root,
            text="Login  →",
            font=("Helvetica", 11, "bold"),
            bg="#C0392B", fg="white",
            relief="flat", cursor="hand2",
            padx=30, pady=8,
            command=self._login
        ).pack(pady=20)

        # Enter key triggers login
        self.root.bind("<Return>", lambda e: self._login())

    def _login(self):
        name = self.name_entry.get().strip()
        cp   = self.cp_var.get()

        if not name:
            messagebox.showwarning("Required", "Please enter your name.")
            return

        # Open main window
        self.root.destroy()

        main_root = tk.Tk()
        from ui.main_window import MainWindow
        app = MainWindow(main_root, name, cp)
        main_root.mainloop()


def main():
    # Check DB connection first
    if not test_connection():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Error",
            "Cannot connect to the local database.\n\n"
            "Make sure MySQL is running and your config.py settings are correct."
        )
        return

    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()