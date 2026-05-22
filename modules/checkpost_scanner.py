# ui/checkpost_scanner.py
# ============================================================
# Checkpost officer screen.
# Officer scans / types ticket number → shows tourist info
# and logs a check-in to checkpost_logs table.
#
# New schema tables used:
#   tourists, checkpost_logs, checkposts, officers
# ============================================================

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.local_db import run_query
from modules.ticket_creator import get_tourist_by_ticket, get_tourist_checkpost_history


class CheckpostScanner:
    def __init__(self, root, officer_id=None, officer_name="Officer", checkpost_name=""):
        self.root           = root
        self.officer_id     = officer_id
        self.officer_name   = officer_name
        self.checkpost_name = checkpost_name
        self.checkpost_id   = self._get_checkpost_id(checkpost_name)

        self.root.title(f"Checkpost Scanner — {checkpost_name}")
        self.root.geometry("1100x700")
        self.root.state("zoomed")
        self.root.configure(bg="#f0f4f8")

        self._build_ui()

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────

    def _get_checkpost_id(self, name):
        rows = run_query(
            "SELECT id FROM checkposts WHERE name = %s AND is_active = 1 LIMIT 1",
            (name,), fetch=True
        )
        return rows[0]["id"] if rows else None

    # ─────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#003399", height=65)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Checkpost Scanner — {self.checkpost_name}",
                 font=("Arial", 18, "bold"), bg="#003399", fg="white"
                 ).pack(side="left", padx=30, pady=15)
        tk.Label(hdr, text=f"Officer: {self.officer_name}",
                 font=("Arial", 11), bg="#003399", fg="#aad4ff"
                 ).pack(side="right", padx=20)

        # Search bar
        search_frame = tk.Frame(self.root, bg="#f0f4f8", pady=20)
        search_frame.pack(fill="x", padx=30)

        tk.Label(search_frame, text="Ticket Number / Passport:",
                 font=("Arial", 12, "bold"), bg="#f0f4f8").pack(side="left")

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     width=30, font=("Arial", 13))
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<Return>", lambda e: self.search_tourist())

        tk.Button(search_frame, text="🔍  Search",
                  bg="#003399", fg="white", font=("Arial", 11, "bold"),
                  command=self.search_tourist
                  ).pack(side="left", padx=5)

        tk.Button(search_frame, text="Clear",
                  bg="#888", fg="white", font=("Arial", 10),
                  command=self.clear_screen
                  ).pack(side="left", padx=5)

        # Result panel
        result_outer = tk.Frame(self.root, bg="#f0f4f8")
        result_outer.pack(fill="both", expand=True, padx=30, pady=10)

        # Left: tourist details
        self.detail_frame = tk.LabelFrame(result_outer, text="Tourist Details",
            font=("Arial", 11, "bold"), bg="white", padx=20, pady=15, width=480)
        self.detail_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.detail_frame.pack_propagate(False)

        self.detail_labels = {}
        fields = [
            ("Ticket Number",  "ticket_number"),
            ("Full Name",      "full_name"),
            ("Passport No.",   "passport_number"),
            ("Nationality",    "nationality"),
            ("Gender",         "gender"),
            ("Date of Birth",  "dob"),
            ("Purpose",        "purpose_name"),
            ("Region",         "region_name"),
            ("Entry Point",    "entry_post_name"),
            ("Exit Point",     "exit_post_name"),
            ("Entry Date",     "entry_date"),
            ("Expiry Date",    "expiry_date"),
            ("Status",         "status"),
        ]
        for row_i, (label, key) in enumerate(fields):
            tk.Label(self.detail_frame, text=f"{label}:",
                     font=("Arial", 9, "bold"), bg="white", anchor="w", width=16
                     ).grid(row=row_i, column=0, sticky="w", pady=3)
            lbl = tk.Label(self.detail_frame, text="—",
                           font=("Arial", 9), bg="white", anchor="w", wraplength=280)
            lbl.grid(row=row_i, column=1, sticky="w", pady=3)
            self.detail_labels[key] = lbl

        # Scan button
        self.scan_btn = tk.Button(self.detail_frame, text="✔  Log Check-In",
            bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
            width=20, command=self.log_checkin, state="disabled")
        self.scan_btn.grid(row=len(fields), column=0, columnspan=2, pady=20)

        self.flag_btn = tk.Button(self.detail_frame, text="⚑  Flag Tourist",
            bg="#e67e22", fg="white", font=("Arial", 10, "bold"),
            width=20, command=self.flag_tourist, state="disabled")
        self.flag_btn.grid(row=len(fields)+1, column=0, columnspan=2)

        # Right: scan history
        history_frame = tk.LabelFrame(result_outer, text="Scan History",
            font=("Arial", 11, "bold"), bg="white", padx=10, pady=10)
        history_frame.pack(side="right", fill="both", expand=True)

        cols = ("Checkpost", "Officer", "Time", "Status")
        self.history_tree = ttk.Treeview(history_frame, columns=cols,
                                         show="headings", height=20)
        for col in cols:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=130)
        self.history_tree.pack(fill="both", expand=True)

        # Status bar at bottom
        self.status_bar = tk.Label(self.root, text="Ready — enter a ticket number to search.",
            font=("Arial", 10), bg="#dce3ec", anchor="w", padx=15)
        self.status_bar.pack(fill="x", side="bottom", ipady=6)

        self.current_tourist = None

    # ─────────────────────────────────────────
    # SEARCH
    # ─────────────────────────────────────────

    def search_tourist(self):
        query = self.search_var.get().strip()
        if not query:
            return

        # Try ticket number first
        tourist = get_tourist_by_ticket(query)

        # If not found, try passport number
        if not tourist:
            rows = run_query(
                """
                SELECT t.*,
                       c.name  AS country_name,
                       p.name  AS purpose_name,
                       r.name  AS region_name,
                       ep.name AS entry_post_name,
                       xp.name AS exit_post_name
                FROM tourists t
                LEFT JOIN countries        c  ON t.country_id    = c.id
                LEFT JOIN purposes         p  ON t.purpose_id    = p.id
                LEFT JOIN trekking_regions r  ON t.region_id     = r.id
                LEFT JOIN checkposts       ep ON t.entry_post_id = ep.id
                LEFT JOIN checkposts       xp ON t.exit_post_id  = xp.id
                WHERE t.passport_number = %s
                ORDER BY t.id DESC LIMIT 1
                """,
                (query.upper(),), fetch=True
            )
            tourist = rows[0] if rows else None

        if not tourist:
            messagebox.showwarning("Not Found",
                f"No tourist found for: {query}")
            self.status_bar.config(text=f"Not found: {query}", fg="red")
            self.current_tourist = None
            self.scan_btn.config(state="disabled")
            self.flag_btn.config(state="disabled")
            return

        self.current_tourist = tourist
        self._populate_details(tourist)
        self._load_history(tourist["ticket_number"])
        self.scan_btn.config(state="normal")
        self.flag_btn.config(state="normal")
        self.status_bar.config(
            text=f"Found: {tourist['ticket_number']} — {tourist.get('first_name','')} {tourist.get('last_name','')}",
            fg="#003399"
        )

    def _populate_details(self, t):
        """Fill detail labels from tourist row."""
        gender_map = {"M": "Male", "F": "Female", "O": "Other"}
        status_map = {0: "Draft", 1: "Applied", 2: "Paid", 3: "Issued", 4: "Rejected"}

        full_name = f"{t.get('first_name','')} {t.get('mid_name') or ''} {t.get('last_name','')}".strip()

        values = {
            "ticket_number":  t.get("ticket_number", "—"),
            "full_name":      full_name or "—",
            "passport_number":t.get("passport_number", "—"),
            "nationality":    t.get("nationality") or t.get("country_name") or "—",
            "gender":         gender_map.get(t.get("gender", ""), "—"),
            "dob":            str(t.get("dob") or "—"),
            "purpose_name":   t.get("purpose_name", "—"),
            "region_name":    t.get("region_name", "—"),
            "entry_post_name":t.get("entry_post_name", "—"),
            "exit_post_name": t.get("exit_post_name", "—"),
            "entry_date":     str(t.get("entry_date") or "—"),
            "expiry_date":    str(t.get("expiry_date") or "—"),
            "status":         status_map.get(t.get("status", 0), "Unknown"),
        }

        # Highlight if expired
        today = datetime.today().date()
        expiry = t.get("expiry_date")
        if expiry and hasattr(expiry, 'year'):
            if expiry < today:
                self.detail_labels["expiry_date"].config(fg="red")
            else:
                self.detail_labels["expiry_date"].config(fg="green")

        for key, val in values.items():
            if key in self.detail_labels:
                self.detail_labels[key].config(text=val)

    def _load_history(self, ticket_number):
        """Load scan history into the treeview."""
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        history = get_tourist_checkpost_history(ticket_number)
        for h in history:
            self.history_tree.insert("", "end", values=(
                h.get("checkpost_name", "—"),
                h.get("officer_name", "—"),
                str(h.get("scan_time", "—")),
                h.get("status", "—"),
            ))

    # ─────────────────────────────────────────
    # LOG CHECK-IN
    # ─────────────────────────────────────────

    def log_checkin(self):
        if not self.current_tourist:
            return

        tourist_id = self.current_tourist["id"]
        ticket_num = self.current_tourist["ticket_number"]

        # Check if permit is expired
        expiry = self.current_tourist.get("expiry_date")
        today  = datetime.today().date()
        if expiry and hasattr(expiry, 'year') and expiry < today:
            if not messagebox.askyesno("Permit Expired",
                    f"This permit expired on {expiry}.\nLog anyway?"):
                return

        result = run_query(
            """
            INSERT INTO checkpost_logs
                (tourist_id, ticket_number, checkpost_id, officer_id, scan_time, status)
            VALUES (%s, %s, %s, %s, %s, 'PASS')
            """,
            (tourist_id, ticket_num, self.checkpost_id, self.officer_id, datetime.now())
        )

        if result:
            messagebox.showinfo("Logged",
                f"✔ Check-in logged for {ticket_num}")
            self.status_bar.config(
                text=f"Logged PASS for {ticket_num} at {datetime.now().strftime('%H:%M:%S')}",
                fg="green"
            )
            self._load_history(ticket_num)
        else:
            messagebox.showerror("Error", "Could not log check-in.")

    def flag_tourist(self):
        if not self.current_tourist:
            return

        tourist_id = self.current_tourist["id"]
        ticket_num = self.current_tourist["ticket_number"]

        result = run_query(
            """
            INSERT INTO checkpost_logs
                (tourist_id, ticket_number, checkpost_id, officer_id, scan_time, status)
            VALUES (%s, %s, %s, %s, %s, 'FLAG')
            """,
            (tourist_id, ticket_num, self.checkpost_id, self.officer_id, datetime.now())
        )

        if result:
            messagebox.showwarning("Flagged", f"⚑ Tourist {ticket_num} has been flagged.")
            self.status_bar.config(text=f"Flagged: {ticket_num}", fg="orange")
            self._load_history(ticket_num)

    def clear_screen(self):
        self.search_var.set("")
        self.current_tourist = None
        for lbl in self.detail_labels.values():
            lbl.config(text="—", fg="black")
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        self.scan_btn.config(state="disabled")
        self.flag_btn.config(state="disabled")
        self.status_bar.config(text="Ready — enter a ticket number to search.", fg="black")


if __name__ == "__main__":
    root = tk.Tk()
    app  = CheckpostScanner(root, officer_name="Test Officer", checkpost_name="Birgunj")
    root.mainloop()