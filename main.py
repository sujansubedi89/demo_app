# main.py
import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import APP_NAME, CHECKPOSTS, UI_ONLY_MODE


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} — Login")
        self.root.geometry("440x420")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - 220
        y = (self.root.winfo_screenheight() // 2) - 210
        self.root.geometry(f"440x420+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # ── Logo + title ──────────────────
        tk.Label(
            self.root, text="🇳🇵",
            font=("Helvetica", 40),
            bg="#1a1a2e"
        ).pack(pady=(20, 5))

        tk.Label(
            self.root,
            text="NEPAL TOURIST TICKETING",
            font=("Helvetica", 14, "bold"),
            bg="#1a1a2e", fg="white"
        ).pack()

        tk.Label(
            self.root,
            text="Officer Login",
            font=("Helvetica", 10),
            bg="#1a1a2e", fg="#AEB6BF"
        ).pack(pady=(2, 5))

        if UI_ONLY_MODE:
            tk.Label(
                self.root,
                text="⚠  UI Development Mode",
                font=("Helvetica", 8, "bold"),
                bg="#F39C12", fg="white",
                padx=8, pady=3
            ).pack(pady=(0, 8))
        else:
            tk.Frame(self.root, bg="#1a1a2e", height=8).pack()

        # ── Login form ────────────────────
        form = tk.Frame(self.root, bg="#1a1a2e")
        form.pack(padx=40, fill="x")

        # Username
        tk.Label(
            form, text="Username",
            font=("Helvetica", 9),
            bg="#1a1a2e", fg="#AEB6BF",
            anchor="w"
        ).pack(fill="x", pady=(8, 2))

        self.username_entry = tk.Entry(
            form,
            font=("Helvetica", 11),
            relief="solid", bd=1,
            bg="white", fg="#2C3E50"
        )
        self.username_entry.pack(fill="x", ipady=6)
        self.username_entry.focus()

        # Password
        tk.Label(
            form, text="Password",
            font=("Helvetica", 9),
            bg="#1a1a2e", fg="#AEB6BF",
            anchor="w"
        ).pack(fill="x", pady=(12, 2))

        pw_frame = tk.Frame(form, bg="white", relief="solid", bd=1)
        pw_frame.pack(fill="x")

        self.password_entry = tk.Entry(
            pw_frame,
            font=("Helvetica", 11),
            relief="flat", bd=0,
            bg="white", fg="#2C3E50",
            show="●"
        )
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=5)

        # Show/hide password toggle
        self.show_pw = False
        self.eye_btn = tk.Button(
            pw_frame,
            text="👁",
            font=("Helvetica", 10),
            bg="white", relief="flat",
            cursor="hand2", bd=0,
            command=self._toggle_password
        )
        self.eye_btn.pack(side="right", padx=4)

        # Checkpost (only shown in UI mode — normally comes from officer profile)
        if UI_ONLY_MODE:
            tk.Label(
                form, text="Checkpost",
                font=("Helvetica", 9),
                bg="#1a1a2e", fg="#AEB6BF",
                anchor="w"
            ).pack(fill="x", pady=(12, 2))

            self.cp_var = tk.StringVar(value=CHECKPOSTS[0])
            ttk.Combobox(
                form,
                textvariable=self.cp_var,
                values=CHECKPOSTS,
                state="readonly",
                font=("Helvetica", 10)
            ).pack(fill="x", ipady=4)
        else:
            self.cp_var = None

        # ── Login button ──────────────────
        tk.Button(
            self.root,
            text="Login  →",
            font=("Helvetica", 12, "bold"),
            bg="#C0392B", fg="white",
            activebackground="#922B21",
            activeforeground="white",
            relief="flat", cursor="hand2",
            pady=10,
            command=self._login
        ).pack(fill="x", padx=40, pady=20)

        # Error message label
        self.error_var = tk.StringVar(value="")
        tk.Label(
            self.root,
            textvariable=self.error_var,
            font=("Helvetica", 9),
            bg="#1a1a2e", fg="#E74C3C"
        ).pack()

        self.root.bind("<Return>", lambda e: self._login())

    def _toggle_password(self):
        self.show_pw = not self.show_pw
        self.password_entry.configure(show="" if self.show_pw else "●")

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_var.set("Please enter username and password.")
            return

        if UI_ONLY_MODE:
            # Skip DB check in UI mode
            self._open_main(username, self.cp_var.get())
            return

        # Verify against database
        from database.local_db import verify_officer
        officer = verify_officer(username, password)

        if not officer:
            self.error_var.set("Invalid username or password.")
            self.password_entry.delete(0, tk.END)
            return

        # Login success
        self._open_main(officer["full_name"], officer.get("role", "officer"))
    def _open_main(self, officer_name, checkpost):
        self.root.destroy()
        main_root = tk.Tk()
        from ui.main_window import MainWindow
        MainWindow(main_root, officer_name, checkpost)
        main_root.mainloop()


def main():
    if not UI_ONLY_MODE:
        from database.local_db import test_connection
        if not test_connection():
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Database Error",
                "Cannot connect to MySQL.\n\n"
                "Make sure MySQL is running and\n"
                "config.py settings are correct."
            )
            return

        from database.sync import start_sync_thread
        start_sync_thread()

    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()