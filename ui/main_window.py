# ui/main_window.py
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk, messagebox
from config import APP_NAME, APP_VERSION, CHECKPOSTS


class MainWindow:
    def __init__(self, root, officer_name, checkpost):
        self.root        = root
        self.officer     = officer_name
        self.checkpost   = checkpost

        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("900x600")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - 450
        y = (self.root.winfo_screenheight() // 2) - 300
        self.root.geometry(f"900x600+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # ── Top header bar ────────────────
        header = tk.Frame(self.root, bg="#C0392B", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🇳🇵  NEPAL TOURIST TICKETING SYSTEM",
            font=("Helvetica", 18, "bold"),
            bg="#C0392B", fg="white"
        ).pack(side="left", padx=20, pady=15)

        # Officer info top right
        info_frame = tk.Frame(header, bg="#C0392B")
        info_frame.pack(side="right", padx=20)

        tk.Label(
            info_frame,
            text=f"Officer: {self.officer}",
            font=("Helvetica", 10, "bold"),
            bg="#C0392B", fg="white"
        ).pack(anchor="e")

        tk.Label(
            info_frame,
            text=f"Checkpost: {self.checkpost}",
            font=("Helvetica", 10),
            bg="#C0392B", fg="#FADBD8"
        ).pack(anchor="e")

        # ── Sub header ────────────────────
        sub = tk.Frame(self.root, bg="#16213e", height=35)
        sub.pack(fill="x")
        sub.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            sub,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg="#16213e", fg="#85C1E9"
        ).pack(side="left", padx=20, pady=8)

        # ── Main content area ─────────────
        content = tk.Frame(self.root, bg="#1a1a2e")
        content.pack(fill="both", expand=True, padx=40, pady=30)

        # Title
        tk.Label(
            content,
            text="Select an Action",
            font=("Helvetica", 14),
            bg="#1a1a2e", fg="#AEB6BF"
        ).pack(pady=(0, 25))

        # ── Big action buttons ─────────────
        buttons_frame = tk.Frame(content, bg="#1a1a2e")
        buttons_frame.pack()

        self._make_big_button(
            buttons_frame,
            icon="🎫",
            title="Create Ticket",
            subtitle="Register new tourist\nand print entry permit",
            color="#1E8449",
            hover="#196F3D",
            command=self._open_create_ticket,
            col=0
        )

        self._make_big_button(
            buttons_frame,
            icon="📷",
            title="Scan QR Code",
            subtitle="Verify tourist at\nthis checkpost",
            color="#1A5276",
            hover="#154360",
            command=self._open_scanner,
            col=1
        )

        self._make_big_button(
            buttons_frame,
            icon="📋",
            title="View All Tickets",
            subtitle="Search and browse\nall tourist records",
            command=self._open_dashboard,
            color="#6C3483",
            hover="#5B2C6F",
            col=2
        )
        # Manage officers link (admin only)
        tk.Button(
            content,
            text="⚙  Manage Officers / Change Password",
            font=("Helvetica", 8),
            bg="#1a1a2e", fg="#5D6D7E",
            relief="flat", cursor="hand2",
            command=self._open_officier_manager
        ).pack(pady=(5, 0))
        # ── Stats bar ─────────────────────
        stats_frame = tk.Frame(content, bg="#16213e", pady=12)
        stats_frame.pack(fill="x", pady=(30, 0))

        self._load_stats(stats_frame)

    def _make_big_button(self, parent, icon, title, subtitle, color, hover, command, col):
        """Creates one large menu button."""
        frame = tk.Frame(parent, bg=color, width=220, height=180, cursor="hand2")
        frame.grid(row=0, column=col, padx=12, pady=5)
        frame.pack_propagate(False)
        frame.grid_propagate(False)

        tk.Label(frame, text=icon,  font=("Helvetica", 36), bg=color, fg="white").pack(pady=(25,5))
        tk.Label(frame, text=title, font=("Helvetica", 13, "bold"), bg=color, fg="white").pack()
        tk.Label(frame, text=subtitle, font=("Helvetica", 9), bg=color, fg="#D5D8DC",
                 justify="center").pack(pady=(4,0))

        # Click anywhere on the button
        for widget in frame.winfo_children():
            widget.bind("<Button-1>", lambda e, cmd=command: cmd())
            widget.bind("<Enter>", lambda e, f=frame, h=hover: f.configure(bg=h))
            widget.bind("<Leave>", lambda e, f=frame, c=color: f.configure(bg=c))

        frame.bind("<Button-1>", lambda e: command())
        frame.bind("<Enter>", lambda e, f=frame, h=hover: f.configure(bg=h))
        frame.bind("<Leave>", lambda e, f=frame, c=color: f.configure(bg=c))

    def _load_stats(self, parent):
        """Loads ticket counts from DB and shows them."""
        from database.local_db import run_query

        total  = run_query("SELECT COUNT(*) as c FROM tourists", fetch=True)
        today  = run_query(
            "SELECT COUNT(*) as c FROM tourists WHERE DATE(created_at) = CURDATE()",
            fetch=True
        )
        scans  = run_query("SELECT COUNT(*) as c FROM checkpost_logs", fetch=True)

        total_count = total[0]["c"]  if total  else 0
        today_count = today[0]["c"]  if today  else 0
        scans_count = scans[0]["c"]  if scans  else 0

        stats = [
            ("Total Tickets",   total_count,  "#F39C12"),
            ("Issued Today",    today_count,  "#27AE60"),
            ("Total QR Scans",  scans_count,  "#2980B9"),
        ]

        for i, (label, value, color) in enumerate(stats):
            col_frame = tk.Frame(parent, bg="#16213e")
            col_frame.pack(side="left", expand=True)

            tk.Label(
                col_frame, text=str(value),
                font=("Helvetica", 22, "bold"),
                bg="#16213e", fg=color
            ).pack()

            tk.Label(
                col_frame, text=label,
                font=("Helvetica", 9),
                bg="#16213e", fg="#AEB6BF"
            ).pack()

            # Divider between stats (not after last)
            if i < len(stats) - 1:
                tk.Frame(parent, bg="#2C3E50", width=1).pack(
                    side="left", fill="y", padx=15, pady=8
                )

    def _open_create_ticket(self):
        from ui.permit_form_ui import TicketUI
        win = tk.Toplevel(self.root)
        TicketUI(win, self.officer, self.checkpost)

    def _open_scanner(self):
        from ui.scanner_ui import ScannerWindow
        win = tk.Toplevel(self.root)
        ScannerWindow(win, self.officer, self.checkpost)

    def _open_dashboard(self):
        from ui.dashboard_ui import DashboardWindow
        win = tk.Toplevel(self.root)
        DashboardWindow(win)

    def _refresh_stats(self):
        """Called after a ticket is created to update the counts."""
        self.status_var.set("Ticket created successfully.")
        # Rebuild stats bar
        for widget in self.root.winfo_children():
            pass  # stats refresh handled on next open
    def _open_officier_manager(self):
        win=tk.Toplevel(self.root)
        win.title("Manage Officiers")
        win.geometry("500x400")
        win.configure(bg="#f0f0f0")
        tk.Label(win,text="OFFICER ACCOUNTS",
        font=("Helvetica",13,"bold"),
        bg="#C0392B",
        fg="white",
        pady=10
        ).pack(fill="x")
        from database.local_db import run_query
        officiers=run_query("SELECT username,full_name,checkpost,is_active FROM officers",fetch=True
        )or []
        cols=("Username","Full Name","Checkpost","Active")
        tree=ttk.Treeview(win,columns=cols,show="headings",height=12)
        for col in cols:
            tree.heading(col,text=col)
            tree.column(col,width=110,anchor="center")
            tree.pack(fill="both",expand=True,padx=15,pady=10)
            for o in officiers:
                tree.insert("", "end", values=(
                    o["username"],
                    o["full_name"],
                    o["checkpost"],
                    "Yes" if o["is_active"] else "No"
                ))
        tk.Label(
            win,
            text="To add officiers run insert into officiers table",
            font=("Helvetica", 10, "italic"),
            bg="#f0f0f0", fg="#E74C3C"
        ).pack(pady=5)
