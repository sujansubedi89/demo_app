# ui/ticket_printer.py
# ============================================================
# Reprint / lookup screen.
# Officer types ticket number → fetches from DB → opens PDF.
# Uses new schema: tourists with JOINed tables.
# ============================================================

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

from modules.ticket_creator import get_tourist_by_ticket, get_tourist_checkpost_history
from modules.pdf_generator  import generate_ticket_pdf
from modules.qr_generator   import get_qr_path
from config import TICKETS_DIR


class TicketPrinter:
    def __init__(self, root, officer_name="Officer", checkpost=""):
        self.root         = root
        self.officer_name = officer_name
        self.checkpost    = checkpost

        self.root.title("Reprint / Lookup Permit")
        self.root.geometry("900x650")
        self.root.configure(bg="#f0f4f8")

        self._build_ui()

    # ─────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#003399", height=60)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Reprint / Lookup Permit",
                 font=("Arial", 16, "bold"), bg="#003399", fg="white"
                 ).pack(side="left", padx=25, pady=15)

        # Search
        sf = tk.Frame(self.root, bg="#f0f4f8", pady=20)
        sf.pack(fill="x", padx=30)
        tk.Label(sf, text="Ticket Number:", font=("Arial", 11, "bold"),
                 bg="#f0f4f8").pack(side="left")
        self.search_var = tk.StringVar()
        e = tk.Entry(sf, textvariable=self.search_var, width=28, font=("Arial", 12))
        e.pack(side="left", padx=10)
        e.bind("<Return>", lambda _: self.lookup())
        tk.Button(sf, text="🔍  Lookup", bg="#003399", fg="white",
                  font=("Arial", 10, "bold"), command=self.lookup
                  ).pack(side="left", padx=5)

        # Details frame
        self.details = tk.LabelFrame(self.root, text="Permit Details",
            font=("Arial", 11, "bold"), bg="white", padx=20, pady=15)
        self.details.pack(fill="x", padx=30, pady=10)

        self.detail_labels = {}
        rows_def = [
            ("Ticket Number",  "ticket_number"),
            ("Full Name",      "full_name"),
            ("Passport No.",   "passport_number"),
            ("Nationality",    "nationality"),
            ("Gender",         "gender"),
            ("Purpose",        "purpose_name"),
            ("Region",         "region_name"),
            ("Entry Point",    "entry_post_name"),
            ("Exit Point",     "exit_post_name"),
            ("Entry Date",     "entry_date"),
            ("Expiry Date",    "expiry_date"),
        ]
        for i, (label, key) in enumerate(rows_def):
            r, c = divmod(i, 3)
            tk.Label(self.details, text=f"{label}:", font=("Arial", 9, "bold"),
                     bg="white", anchor="w", width=14
                     ).grid(row=r*2, column=c, sticky="w", padx=15, pady=(8, 0))
            lbl = tk.Label(self.details, text="—", font=("Arial", 9),
                           bg="white", anchor="w", width=22)
            lbl.grid(row=r*2+1, column=c, sticky="w", padx=15)
            self.detail_labels[key] = lbl

        # Scan history
        hist_frame = tk.LabelFrame(self.root, text="Scan History",
            font=("Arial", 11, "bold"), bg="white", padx=10, pady=10)
        hist_frame.pack(fill="both", expand=True, padx=30, pady=5)

        cols = ("Checkpost", "Officer", "Time", "Status")
        self.hist_tree = ttk.Treeview(hist_frame, columns=cols, show="headings", height=6)
        for col in cols:
            self.hist_tree.heading(col, text=col)
            self.hist_tree.column(col, width=180)
        self.hist_tree.pack(fill="both", expand=True)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#f0f4f8", pady=15)
        btn_frame.pack(fill="x", padx=30)

        self.print_btn = tk.Button(btn_frame, text="🖨  Reprint PDF",
            bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
            width=18, command=self.reprint, state="disabled")
        self.print_btn.pack(side="right", padx=10)

        self.open_btn = tk.Button(btn_frame, text="📂  Open PDF Folder",
            bg="#2980b9", fg="white", font=("Arial", 10),
            width=18, command=self.open_folder)
        self.open_btn.pack(side="right", padx=5)

        self.current_tourist = None

    # ─────────────────────────────────────────
    # LOOKUP
    # ─────────────────────────────────────────

    def lookup(self):
        ticket = self.search_var.get().strip()
        if not ticket:
            return

        tourist = get_tourist_by_ticket(ticket)
        if not tourist:
            messagebox.showwarning("Not Found", f"No permit found for: {ticket}")
            return

        self.current_tourist = tourist
        gender_map = {"M": "Male", "F": "Female", "O": "Other"}
        full_name = f"{tourist.get('first_name','')} {tourist.get('mid_name') or ''} {tourist.get('last_name','')}".strip()

        values = {
            "ticket_number":   tourist.get("ticket_number", "—"),
            "full_name":       full_name,
            "passport_number": tourist.get("passport_number", "—"),
            "nationality":     tourist.get("nationality") or tourist.get("country_name", "—"),
            "gender":          gender_map.get(tourist.get("gender", ""), "—"),
            "purpose_name":    tourist.get("purpose_name", "—"),
            "region_name":     tourist.get("region_name", "—"),
            "entry_post_name": tourist.get("entry_post_name", "—"),
            "exit_post_name":  tourist.get("exit_post_name", "—"),
            "entry_date":      str(tourist.get("entry_date") or "—"),
            "expiry_date":     str(tourist.get("expiry_date") or "—"),
        }
        for key, val in values.items():
            if key in self.detail_labels:
                self.detail_labels[key].config(text=val)

        # Scan history
        for row in self.hist_tree.get_children():
            self.hist_tree.delete(row)
        history = get_tourist_checkpost_history(ticket)
        for h in history:
            self.hist_tree.insert("", "end", values=(
                h.get("checkpost_name", "—"),
                h.get("officer_name", "—"),
                str(h.get("scan_time", "—")),
                h.get("status", "—"),
            ))

        self.print_btn.config(state="normal")

    # ─────────────────────────────────────────
    # REPRINT
    # ─────────────────────────────────────────

    def reprint(self):
        if not self.current_tourist:
            return

        t = self.current_tourist
        full_name = f"{t.get('first_name','')} {t.get('mid_name') or ''} {t.get('last_name','')}".strip()

        tourist_data = {
            "ticket_number":   t["ticket_number"],
            "full_name":       full_name,
            "passport_number": t.get("passport_number", ""),
            "nationality":     t.get("nationality") or t.get("country_name", ""),
            "gender":          t.get("gender", ""),
            "photo_path":      t.get("photo_path"),
            "destination":     t.get("region_name", ""),
            "sub_area":        t.get("region_name", ""),
            "entry_date":      t.get("entry_date"),
            "expiry_date":     t.get("expiry_date"),
            "permit_code":     t["ticket_number"],
            "permit_ref":      t["ticket_number"],
            "permit_cost":     "NPR. 1000 (13% VAT included)",
            "el_code":         "",
            "serial_code":     "",
            "agency":          self.officer_name,
            "created_by":      t.get("created_by", ""),
            "created_at":      t.get("created_at"),
        }

        history = get_tourist_checkpost_history(t["ticket_number"])

        try:
            pdf_path = generate_ticket_pdf(tourist_data, scan_history=history)
            messagebox.showinfo("Reprinted", f"PDF saved:\n{pdf_path}")
            try:
                os.startfile(pdf_path)
            except Exception:
                subprocess.Popen(["start", pdf_path], shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate PDF:\n{e}")

    def open_folder(self):
        try:
            os.startfile(TICKETS_DIR)
        except Exception:
            subprocess.Popen(["explorer", TICKETS_DIR], shell=True)


if __name__ == "__main__":
    root = tk.Tk()
    app  = TicketPrinter(root, officer_name="Test Officer", checkpost="Birgunj")
    root.mainloop()