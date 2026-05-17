# ui/dashboard_ui.py
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk, messagebox
from database.local_db import run_query


class DashboardWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("All Tourist Records")
        self.root.geometry("900x550")
        self.root.configure(bg="#f0f0f0")

        self._build_ui()
        self._load_records()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#6C3483", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="📋  ALL TOURIST RECORDS",
            font=("Helvetica", 13, "bold"),
            bg="#6C3483", fg="white"
        ).pack(side="left", padx=20, pady=12)

        # Search bar
        search_frame = tk.Frame(self.root, bg="#f0f0f0", pady=8)
        search_frame.pack(fill="x", padx=20)

        tk.Label(
            search_frame,
            text="Search:",
            font=("Helvetica", 10),
            bg="#f0f0f0"
        ).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_records())

        tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Helvetica", 10),
            width=30, relief="solid"
        ).pack(side="left", padx=8, ipady=4)

        tk.Label(
            search_frame,
            text="(searches name, passport, nationality)",
            font=("Helvetica", 8),
            bg="#f0f0f0", fg="gray"
        ).pack(side="left")

        # Table
        cols = ("Ticket No", "Name", "Nationality", "Passport", "Entry", "Expiry", "Synced")
        self.tree = ttk.Treeview(
            self.root,
            columns=cols,
            show="headings",
            height=20
        )

        widths = [130, 180, 120, 110, 90, 90, 60]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        # Scrollbar for table
        scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(20,0), pady=5)
        scroll.pack(side="left", fill="y", pady=5)

        # Row count
        self.count_var = tk.StringVar(value="")
        tk.Label(
            self.root,
            textvariable=self.count_var,
            font=("Helvetica", 9),
            bg="#f0f0f0", fg="gray"
        ).pack(pady=5)

    def _load_records(self):
        """Loads all tourists from DB into self.all_rows."""
        rows = run_query(
            "SELECT ticket_number, full_name, nationality, passport_number, "
            "entry_date, expiry_date, synced FROM tourists ORDER BY id DESC",
            fetch=True
        ) or []
        self.all_rows = rows
        self._populate_table(rows)

    def _populate_table(self, rows):
        """Clears and fills the table with given rows."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            synced = "✅" if row["synced"] else "⏳"
            self.tree.insert("", "end", values=(
                row["ticket_number"],
                row["full_name"],
                row["nationality"],
                row["passport_number"],
                str(row["entry_date"]),
                str(row["expiry_date"]),
                synced,
            ))

        self.count_var.set(f"{len(rows)} record(s) found")

    def _filter_records(self):
        """Filters table based on search box."""
        query = self.search_var.get().lower()
        if not query:
            self._populate_table(self.all_rows)
            return

        filtered = [
            r for r in self.all_rows
            if query in r["full_name"].lower()
            or query in r["nationality"].lower()
            or query in r["passport_number"].lower()
            or query in r["ticket_number"].lower()
        ]
        self._populate_table(filtered)