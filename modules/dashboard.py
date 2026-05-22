# ui/dashboard.py
# ============================================================
# Admin dashboard — summary stats and recent permits.
# Uses new schema: tourists, countries, purposes,
#                  trekking_regions, checkpost_logs
# ============================================================

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date

from database.local_db import run_query


class Dashboard:
    def __init__(self, root, officer_name="Admin", checkpost=""):
        self.root         = root
        self.officer_name = officer_name
        self.checkpost    = checkpost

        self.root.title("Dashboard — Nepal Permit Management")
        self.root.geometry("1200x750")
        self.root.state("zoomed")
        self.root.configure(bg="#f0f4f8")

        self._build_ui()
        self.refresh_data()

    # ─────────────────────────────────────────
    # UI LAYOUT
    # ─────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#003399", height=65)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Nepal Entry Permit — Dashboard",
                 font=("Arial", 18, "bold"), bg="#003399", fg="white"
                 ).pack(side="left", padx=30, pady=15)
        tk.Label(hdr, text=f"Officer: {self.officer_name}  |  {self.checkpost}  |  {date.today()}",
                 font=("Arial", 10), bg="#003399", fg="#aad4ff"
                 ).pack(side="right", padx=20)

        # Stat cards row
        self.cards_frame = tk.Frame(self.root, bg="#f0f4f8", pady=20)
        self.cards_frame.pack(fill="x", padx=30)

        self.card_vars = {}
        card_defs = [
            ("total_today",     "Today's Permits",   "#27ae60"),
            ("total_all",       "Total Permits",      "#2980b9"),
            ("total_issued",    "Issued",             "#8e44ad"),
            ("total_expired",   "Expired Today",      "#e74c3c"),
            ("total_saarc",     "SAARC Tourists",     "#16a085"),
            ("total_nonsaarc",  "Non-SAARC Tourists", "#d35400"),
        ]
        for key, label, color in card_defs:
            var = tk.StringVar(value="—")
            self.card_vars[key] = var
            self._make_card(self.cards_frame, label, var, color)

        # Refresh button
        tk.Button(self.root, text="⟳  Refresh",
                  bg="#003399", fg="white", font=("Arial", 10, "bold"),
                  command=self.refresh_data
                  ).pack(anchor="ne", padx=35, pady=5)

        # Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=30, pady=10)

        # Tab 1: Recent permits
        tab1 = tk.Frame(notebook, bg="white")
        notebook.add(tab1, text="Recent Permits")
        self._build_permits_tab(tab1)

        # Tab 2: By purpose
        tab2 = tk.Frame(notebook, bg="white")
        notebook.add(tab2, text="By Purpose")
        self._build_purpose_tab(tab2)

        # Tab 3: By region
        tab3 = tk.Frame(notebook, bg="white")
        notebook.add(tab3, text="By Region")
        self._build_region_tab(tab3)

        # Tab 4: Recent scans
        tab4 = tk.Frame(notebook, bg="white")
        notebook.add(tab4, text="Recent Scans")
        self._build_scans_tab(tab4)

        # Footer
        footer = tk.Frame(self.root, bg="#4CAF50", height=35)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2026 Nepal Permit Management System",
                 bg="#4CAF50", fg="white").pack(pady=8)

    def _make_card(self, parent, label, var, color):
        card = tk.Frame(parent, bg=color, width=160, height=90, relief="flat")
        card.pack(side="left", padx=8, pady=5)
        card.pack_propagate(False)
        tk.Label(card, text=label, bg=color, fg="white",
                 font=("Arial", 9, "bold"), wraplength=140).pack(pady=(14, 2))
        tk.Label(card, textvariable=var, bg=color, fg="white",
                 font=("Arial", 22, "bold")).pack()

    def _build_permits_tab(self, parent):
        cols = ("Ticket", "Name", "Passport", "Nationality", "Purpose",
                "Region", "Entry Date", "Expiry", "Status")
        self.permit_tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        widths = [130, 160, 110, 110, 90, 150, 100, 100, 80]
        for col, w in zip(cols, widths):
            self.permit_tree.heading(col, text=col)
            self.permit_tree.column(col, width=w)

        sb = ttk.Scrollbar(parent, orient="vertical", command=self.permit_tree.yview)
        self.permit_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.permit_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def _build_purpose_tab(self, parent):
        cols = ("Purpose", "Count")
        self.purpose_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        for col in cols:
            self.purpose_tree.heading(col, text=col)
            self.purpose_tree.column(col, width=200)
        self.purpose_tree.pack(fill="both", expand=True, padx=20, pady=20)

    def _build_region_tab(self, parent):
        cols = ("Region", "Count")
        self.region_tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for col in cols:
            self.region_tree.heading(col, text=col)
            self.region_tree.column(col, width=250)
        self.region_tree.pack(fill="both", expand=True, padx=20, pady=20)

    def _build_scans_tab(self, parent):
        cols = ("Ticket", "Tourist", "Checkpost", "Officer", "Time", "Status")
        self.scans_tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        widths = [130, 160, 140, 130, 150, 80]
        for col, w in zip(cols, widths):
            self.scans_tree.heading(col, text=col)
            self.scans_tree.column(col, width=w)
        sb2 = ttk.Scrollbar(parent, orient="vertical", command=self.scans_tree.yview)
        self.scans_tree.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.scans_tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ─────────────────────────────────────────
    # DATA LOADING
    # ─────────────────────────────────────────

    def refresh_data(self):
        today = date.today()

        # ── Stat cards ──────────────────────────────
        def q(sql, params=()):
            rows = run_query(sql, params, fetch=True)
            return rows[0]["cnt"] if rows else 0

        self.card_vars["total_today"].set(
            q("SELECT COUNT(*) AS cnt FROM tourists WHERE DATE(created_at) = %s", (today,)))
        self.card_vars["total_all"].set(
            q("SELECT COUNT(*) AS cnt FROM tourists"))
        self.card_vars["total_issued"].set(
            q("SELECT COUNT(*) AS cnt FROM tourists WHERE status = 3"))
        self.card_vars["total_expired"].set(
            q("SELECT COUNT(*) AS cnt FROM tourists WHERE expiry_date < %s", (today,)))
        self.card_vars["total_saarc"].set(
            q("""SELECT COUNT(*) AS cnt FROM tourists t
                 JOIN countries c ON t.country_id = c.id
                 WHERE c.is_saarc = 1"""))
        self.card_vars["total_nonsaarc"].set(
            q("""SELECT COUNT(*) AS cnt FROM tourists t
                 JOIN countries c ON t.country_id = c.id
                 WHERE c.is_saarc = 0"""))

        # ── Recent permits ───────────────────────────
        for row in self.permit_tree.get_children():
            self.permit_tree.delete(row)

        status_map = {0: "Draft", 1: "Applied", 2: "Paid", 3: "Issued", 4: "Rejected"}
        permits = run_query(
            """
            SELECT t.ticket_number,
                   CONCAT(t.first_name, ' ', COALESCE(t.mid_name,''), ' ', t.last_name) AS full_name,
                   t.passport_number,
                   COALESCE(c.name, t.nationality) AS nationality,
                   p.name  AS purpose_name,
                   r.name  AS region_name,
                   t.entry_date, t.expiry_date, t.status
            FROM tourists t
            LEFT JOIN countries        c ON t.country_id  = c.id
            LEFT JOIN purposes         p ON t.purpose_id  = p.id
            LEFT JOIN trekking_regions r ON t.region_id   = r.id
            ORDER BY t.id DESC LIMIT 100
            """,
            fetch=True
        ) or []

        for p in permits:
            tag = "expired" if (p["expiry_date"] and p["expiry_date"] < today) else ""
            self.permit_tree.insert("", "end", tags=(tag,), values=(
                p["ticket_number"],
                (p["full_name"] or "").strip(),
                p["passport_number"],
                p["nationality"] or "—",
                p["purpose_name"] or "—",
                p["region_name"]  or "—",
                str(p["entry_date"]  or ""),
                str(p["expiry_date"] or ""),
                status_map.get(p["status"], "—"),
            ))
        self.permit_tree.tag_configure("expired", foreground="red")

        # ── By purpose ───────────────────────────────
        for row in self.purpose_tree.get_children():
            self.purpose_tree.delete(row)

        purpose_rows = run_query(
            """
            SELECT p.name AS purpose_name, COUNT(t.id) AS cnt
            FROM purposes p
            LEFT JOIN tourists t ON t.purpose_id = p.id
            GROUP BY p.id, p.name ORDER BY cnt DESC
            """,
            fetch=True
        ) or []
        for pr in purpose_rows:
            self.purpose_tree.insert("", "end", values=(pr["purpose_name"], pr["cnt"]))

        # ── By region ────────────────────────────────
        for row in self.region_tree.get_children():
            self.region_tree.delete(row)

        region_rows = run_query(
            """
            SELECT r.name AS region_name, COUNT(t.id) AS cnt
            FROM trekking_regions r
            LEFT JOIN tourists t ON t.region_id = r.id
            GROUP BY r.id, r.name ORDER BY cnt DESC
            """,
            fetch=True
        ) or []
        for rr in region_rows:
            self.region_tree.insert("", "end", values=(rr["region_name"], rr["cnt"]))

        # ── Recent scans ─────────────────────────────
        for row in self.scans_tree.get_children():
            self.scans_tree.delete(row)

        scans = run_query(
            """
            SELECT cl.ticket_number,
                   CONCAT(t.first_name, ' ', t.last_name) AS tourist_name,
                   cp.name  AS checkpost_name,
                   o.full_name AS officer_name,
                   cl.scan_time, cl.status
            FROM checkpost_logs cl
            LEFT JOIN tourists  t  ON cl.tourist_id   = t.id
            LEFT JOIN checkposts cp ON cl.checkpost_id = cp.id
            LEFT JOIN officers   o  ON cl.officer_id   = o.id
            ORDER BY cl.scan_time DESC LIMIT 100
            """,
            fetch=True
        ) or []

        for s in scans:
            self.scans_tree.insert("", "end", values=(
                s["ticket_number"],
                (s["tourist_name"] or "").strip(),
                s["checkpost_name"] or "—",
                s["officer_name"]   or "—",
                str(s["scan_time"]  or ""),
                s["status"]         or "—",
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app  = Dashboard(root, officer_name="Admin", checkpost="Head Office")
    root.mainloop()