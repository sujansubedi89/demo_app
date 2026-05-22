import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import subprocess
import shutil

from modules.ticket_creator import (
    save_tourist,
    fetch_countries, fetch_occupations,
    fetch_purposes, fetch_regions, fetch_checkposts
)
from modules.qr_generator  import generate_qr
from modules.pdf_generator import generate_ticket_pdf
from config import PHOTOS_DIR

try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False


# ─────────────────────────────────────────
# Autocomplete combobox
# ─────────────────────────────────────────

class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list)
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list

    def handle_keyrelease(self, event):
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down',
                            'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Return'):
            return
        value = self.get()
        if not value:
            self['values'] = self._completion_list
            return
        hits = [i for i in self._completion_list if i.lower().startswith(value.lower())]
        if not hits:
            hits = [i for i in self._completion_list if value.lower() in i.lower()]
        self['values'] = hits if hits else self._completion_list


# ─────────────────────────────────────────
# Main UI class
# ─────────────────────────────────────────

class TicketUI:
    def __init__(self, root, officer_name="Officer", checkpost=""):
        self.root      = root
        self.officer   = officer_name
        self.checkpost = checkpost

        self.root.title("Online Entry Permit Entry Form")
        self.root.geometry("1200x750")
        self.root.state('zoomed')
        self.root.configure(bg="#f2f2f2")

        # ── Load dropdown data from DB ──────────────
        # These come from the new schema tables
        self.countries   = fetch_countries()   # → countries table
        self.occupations = fetch_occupations() # → occupations table
        self.purposes    = fetch_purposes()    # → purposes table (Trekking/Tourism/Research)
        self.regions     = fetch_regions()     # → trekking_regions table
        self.checkposts  = fetch_checkposts()  # → checkposts table

        # Fallback if DB not connected yet
        if not self.countries:
            self.countries = [
                "Afghanistan","Albania","Algeria","Andorra","Angola","Argentina",
                "Armenia","Australia","Austria","Bangladesh","Belgium","Bhutan",
                "Brazil","Canada","China","Denmark","Egypt","Finland","France",
                "Germany","Greece","Iceland","India","Indonesia","Italy","Japan",
                "Malaysia","Maldives","Nepal","Netherlands","New Zealand","Norway",
                "Pakistan","Philippines","Poland","Portugal","Russia","Singapore",
                "Spain","Sri Lanka","Sweden","Switzerland","Thailand",
                "United Kingdom","United States","Vietnam"
            ]
        if not self.occupations:
            self.occupations = [
                "Student","Engineer","Researcher","Journalist","Consultant",
                "Doctor","Business Owner","Photographer","Other"
            ]
        if not self.purposes:
            self.purposes = ["Trekking", "Tourism", "Research"]

        if not self.regions:
            self.regions = [
                "Everest Region", "Annapurna Circuit", "Annapurna Base Camp",
                "Langtang Region", "Manaslu Circuit", "Upper Mustang",
                "Kanchenjunga Region", "Dolpo Region"
            ]
        if not self.checkposts:
            self.checkposts = [
                "Birgunj", "Bhairahawa", "Kakarbhitta",
                "Dhangadhi", "Mahendranagar", "Rasuwagadhi", "Tatopani"
            ]

        self.visitor_fields_data = []
        self._build_ui()

    # ══════════════════════════════════════
    # UI BUILDER
    # ══════════════════════════════════════

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="white", height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="Online Entry Permit",
                 font=("Arial", 22, "bold"), bg="white", fg="#4CAF50"
                 ).pack(side="left", padx=35, pady=15)
        tk.Label(header, text=f"Officer: {self.officer}  |  {self.checkpost}",
                 font=("Arial", 10), bg="white", fg="gray"
                 ).pack(side="right", padx=20)

        # Footer
        footer = tk.Frame(self.root, bg="#4CAF50", height=40)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="© 2026 Nepal Ticket Management System",
                 bg="#4CAF50", fg="white").pack(pady=10)

        # Scrollable canvas
        self.main_canvas = tk.Canvas(self.root, bg="#f2f2f2", highlightthickness=0)
        self.scrollbar   = ttk.Scrollbar(self.root, orient="vertical",
                                         command=self.main_canvas.yview)
        self.scrollable_container = tk.Frame(self.main_canvas, bg="#f2f2f2")

        self.scrollable_container.bind("<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")))

        self.canvas_window = self.main_canvas.create_window(
            (0, 0), window=self.scrollable_container, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_canvas.bind('<Configure>',
            lambda e: self.main_canvas.itemconfig(self.canvas_window, width=e.width))
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Section A: Visitor Count ──────────────────
        visitor_frame = tk.LabelFrame(self.scrollable_container,
            text="A. Visitor Information",
            font=("Arial", 11, "bold"), bg="white", padx=20, pady=20)
        visitor_frame.pack(fill="x", padx=30, pady=10)

        tk.Label(visitor_frame, text="Select Total Visitors *",
                 bg="white", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.visitor_combo = ttk.Combobox(visitor_frame,
            values=[str(x) for x in range(1, 16)], width=20, state="readonly")
        self.visitor_combo.grid(row=1, column=0, pady=10, sticky="w")

        tk.Button(visitor_frame, text="Generate Visitor Forms",
                  bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                  command=self.generate_visitor_forms
                  ).grid(row=1, column=1, padx=10)

        self.dynamic_form_frame = tk.Frame(visitor_frame, bg="white")
        self.dynamic_form_frame.grid_forget()

        # ── Section B: Visit Information ─────────────
        self.visit_frame = tk.LabelFrame(self.scrollable_container,
            text="B. Visit Information",
            font=("Arial", 11, "bold"), bg="white", padx=20, pady=20)
        self.visit_frame.pack(fill="x", padx=30, pady=10)

        # Purpose: Trekking / Tourism / Research (from purposes table)
        tk.Label(self.visit_frame, text="Purpose *", bg="white").grid(
            row=0, column=0, sticky="w")
        self.purpose = ttk.Combobox(self.visit_frame,
            values=self.purposes, width=40, state="readonly")
        self.purpose.grid(row=1, column=0, padx=5, pady=5)

        # Region: from trekking_regions table
        tk.Label(self.visit_frame, text="Trekking Region / Area *", bg="white").grid(
            row=0, column=1, sticky="w")
        self.region = ttk.Combobox(self.visit_frame,
            values=self.regions, width=50, state="readonly")
        self.region.grid(row=1, column=1, padx=5, pady=5)

        # Entry Point: from checkposts table
        tk.Label(self.visit_frame, text="Entry Point *", bg="white").grid(
            row=2, column=0, sticky="w")
        self.entry_point = ttk.Combobox(self.visit_frame,
            values=self.checkposts, width=40, state="readonly")
        self.entry_point.grid(row=3, column=0, padx=5, pady=5)

        # Exit Point: from checkposts table
        tk.Label(self.visit_frame, text="Exit Point *", bg="white").grid(
            row=2, column=1, sticky="w")
        self.exit_point = ttk.Combobox(self.visit_frame,
            values=self.checkposts, width=40, state="readonly")
        self.exit_point.grid(row=3, column=1, padx=5, pady=5)

        # Start Date
        tk.Label(self.visit_frame, text="Start Date *", bg="white").grid(
            row=4, column=0, sticky="w")
        if HAS_TKCALENDAR:
            self.start_date = DateEntry(self.visit_frame, width=38,
                background='darkgreen', foreground='white', borderwidth=2,
                mindate=datetime.today())
        else:
            self.start_date = tk.Entry(self.visit_frame, width=43)
            self.start_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.start_date.grid(row=5, column=0, padx=5, pady=5)

        # End Date
        tk.Label(self.visit_frame, text="End Date *", bg="white").grid(
            row=4, column=1, sticky="w")
        if HAS_TKCALENDAR:
            self.end_date = DateEntry(self.visit_frame, width=38,
                background='darkgreen', foreground='white', borderwidth=2,
                mindate=datetime.today())
        else:
            self.end_date = tk.Entry(self.visit_frame, width=43)
            self.end_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.end_date.grid(row=5, column=1, padx=5, pady=5)

        # ── Section C: Guide / Porter ─────────────────
        self.guide_frame = tk.LabelFrame(self.scrollable_container,
            text="C. Support Services (Optional)",
            font=("Arial", 11, "bold"), bg="white", padx=20, pady=20)
        self.guide_frame.pack(fill="x", padx=30, pady=10)

        tk.Label(self.guide_frame, text="Guide Name",     bg="white").grid(row=0, column=0, sticky="w")
        self.guide_name = tk.Entry(self.guide_frame, width=35)
        self.guide_name.grid(row=1, column=0, padx=5, pady=5)

        tk.Label(self.guide_frame, text="Guide Contact",  bg="white").grid(row=0, column=1, sticky="w")
        self.guide_contact = tk.Entry(self.guide_frame, width=35)
        self.guide_contact.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.guide_frame, text="Number of Guides", bg="white").grid(row=0, column=2, sticky="w")
        self.guide_total = tk.Entry(self.guide_frame, width=25)
        self.guide_total.grid(row=1, column=2, padx=5, pady=5)

        tk.Label(self.guide_frame, text="Guide Trained?", bg="white").grid(row=0, column=3, sticky="w")
        self.guide_trained = ttk.Combobox(self.guide_frame,
            values=["Yes", "No"], width=10, state="readonly")
        self.guide_trained.grid(row=1, column=3, padx=5, pady=5)

        ttk.Separator(self.guide_frame, orient='horizontal').grid(
            row=2, column=0, columnspan=4, sticky='ew', pady=15)

        tk.Label(self.guide_frame, text="Porter Name",    bg="white").grid(row=3, column=0, sticky="w")
        self.porter_name = tk.Entry(self.guide_frame, width=35)
        self.porter_name.grid(row=4, column=0, padx=5, pady=5)

        tk.Label(self.guide_frame, text="Porter Contact", bg="white").grid(row=3, column=1, sticky="w")
        self.porter_contact = tk.Entry(self.guide_frame, width=35)
        self.porter_contact.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(self.guide_frame, text="Number of Porters", bg="white").grid(row=3, column=2, sticky="w")
        self.porter_total = tk.Entry(self.guide_frame, width=25)
        self.porter_total.grid(row=4, column=2, padx=5, pady=5)

        # ── Buttons ───────────────────────────────────
        button_frame = tk.Frame(self.scrollable_container, bg="#f2f2f2")
        button_frame.pack(fill="x", padx=30, pady=20)

        tk.Button(button_frame, text="Confirm & Print Permit",
                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  width=22, height=2,
                  command=self.validate_and_submit
                  ).pack(side="right", padx=10)

        tk.Button(button_frame, text="Cancel",
                  bg="#d9534f", fg="white", font=("Arial", 12, "bold"),
                  width=12, height=2,
                  command=self.reset_entire_ui
                  ).pack(side="right", padx=10)

    # ══════════════════════════════════════
    # SCROLL
    # ══════════════════════════════════════

    def _on_mousewheel(self, event):
        try:
            if event.delta < 0:
                self.main_canvas.yview_scroll(1, "units")
            else:
                self.main_canvas.yview_scroll(-1, "units")
        except Exception:
            pass

    # ══════════════════════════════════════
    # VISITOR FORMS (Section A dynamic rows)
    # ══════════════════════════════════════

    def generate_visitor_forms(self):
        try:
            total = int(self.visitor_combo.get())
        except ValueError:
            messagebox.showwarning("Selection Missing",
                "Please select total visitors first.")
            return

        for w in self.dynamic_form_frame.winfo_children():
            w.destroy()
        self.visitor_fields_data.clear()

        if total > 0:
            self.dynamic_form_frame.grid(
                row=2, column=0, columnspan=5, pady=10, sticky="ew")

            for i in range(total):
                refs = {}
                form = tk.LabelFrame(self.dynamic_form_frame,
                    text=f"Visitor {i+1} Details",
                    bg="white", padx=15, pady=15)
                form.pack(fill="x", pady=10, padx=5)

                # Row 0 labels
                for col, txt in enumerate(["First Name *", "Middle Name",
                                           "Last Name *", "Passport No. *"]):
                    tk.Label(form, text=txt, bg="white").grid(row=0, column=col, sticky="w")

                # Row 1 entries
                fn = tk.Entry(form, width=22); fn.grid(row=1, column=0, padx=5, pady=5)
                mn = tk.Entry(form, width=22); mn.grid(row=1, column=1, padx=5, pady=5)
                ln = tk.Entry(form, width=22); ln.grid(row=1, column=2, padx=5, pady=5)
                pp = tk.Entry(form, width=22); pp.grid(row=1, column=3, padx=5, pady=5)
                refs['first_name'] = fn
                refs['mid_name']   = mn
                refs['last_name']  = ln
                refs['passport']   = pp

                # Row 2 labels
                for col, txt in enumerate(["Gender *", "Date of Birth (MM/DD/YYYY) *",
                                           "Country *", "Occupation *"]):
                    tk.Label(form, text=txt, bg="white").grid(row=2, column=col, sticky="w")

                # Row 3
                gd = ttk.Combobox(form, values=["Male", "Female", "Other"],
                                  width=19, state="readonly")
                gd.grid(row=3, column=0, padx=5, pady=5)
                refs['gender'] = gd

                dob = tk.Entry(form, width=22, fg="gray")
                dob.insert(0, "MM/DD/YYYY")
                dob.bind("<FocusIn>",   lambda e, x=dob: self._clear_dob(x))
                dob.bind("<FocusOut>",  lambda e, x=dob: self._put_dob(x))
                dob.bind("<KeyRelease>",lambda e, x=dob: self._fmt_dob(x))
                dob.grid(row=3, column=1, padx=5, pady=5)
                refs['dob'] = dob

                ct = AutocompleteCombobox(form, width=19)
                ct.set_completion_list(self.countries)
                ct.grid(row=3, column=2, padx=5, pady=5)
                refs['country'] = ct

                oc = ttk.Combobox(form, values=self.occupations, width=19, state="readonly")
                oc.grid(row=3, column=3, padx=5, pady=5)
                refs['occupation'] = oc

                # Row 4/5 photo
                tk.Label(form, text="Photo Upload (JPG/PNG, Max 2MB) *",
                         bg="white").grid(row=4, column=0, sticky="w")
                ph_label = tk.Label(form, text="No File Selected", bg="white", fg="gray")
                ph_label.grid(row=5, column=0, sticky="w", padx=5)
                refs['photo'] = ph_label
                tk.Button(form, text="Upload Photo",
                          command=lambda lbl=ph_label: self.upload_photo(lbl)
                          ).grid(row=5, column=1, padx=5, sticky="w")

                self.visitor_fields_data.append(refs)
        else:
            self.dynamic_form_frame.grid_forget()
    def parse_dob(dob_str):
        """Returns YYYY-MM-DD string or None if invalid."""
        if not dob_str or dob_str.strip() == "":
            return None
        from datetime import datetime
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(dob_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None  # invalid — will show error to user
    def _clear_dob(self, entry):
        if entry.get() == "MM/DD/YYYY":
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def _put_dob(self, entry):
        if not entry.get():
            entry.insert(0, "MM/DD/YYYY")
            entry.config(fg="gray")

    def _fmt_dob(self, entry):
        text    = entry.get().replace("/", "")
        cleaned = "".join(c for c in text if c.isdigit())[:8]
        fmt = ""
        if len(cleaned) > 0: fmt += cleaned[:2]
        if len(cleaned) > 2: fmt += "/" + cleaned[2:4]
        if len(cleaned) > 4: fmt += "/" + cleaned[4:8]
        entry.delete(0, tk.END)
        entry.insert(0, fmt)

    def upload_photo(self, label_widget):
        path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png']:
            messagebox.showerror("Format Error", "Must be .jpg or .png")
            return
        if (os.path.getsize(path) / (1024 * 1024)) > 2.0:
            messagebox.showerror("File Too Large", "Max size is 2MB.")
            return
        label_widget.config(text=path, fg="green")

    def reset_entire_ui(self):
        if messagebox.askyesno("Cancel", "Reset and clear all data?"):
            self.visitor_combo.set('')
            self.purpose.set('')
            self.region.set('')
            self.entry_point.set('')
            self.exit_point.set('')
            self.guide_name.delete(0, tk.END)
            self.guide_contact.delete(0, tk.END)
            self.guide_total.delete(0, tk.END)
            self.guide_trained.set('')
            self.porter_name.delete(0, tk.END)
            self.porter_contact.delete(0, tk.END)
            self.porter_total.delete(0, tk.END)
            for w in self.dynamic_form_frame.winfo_children():
                w.destroy()
            self.visitor_fields_data.clear()

    # ══════════════════════════════════════
    # VALIDATE
    # ══════════════════════════════════════

    def validate_and_submit(self):
        if not self.visitor_fields_data:
            messagebox.showerror("Validation Error",
                "Please generate and fill at least one visitor form.")
            return

        for i, v in enumerate(self.visitor_fields_data):
            n = i + 1
            if not v['first_name'].get().strip() or not v['last_name'].get().strip():
                messagebox.showerror("Validation Error", f"Name is empty for Visitor {n}.")
                return
            if not v['passport'].get().strip():
                messagebox.showerror("Validation Error", f"Passport required for Visitor {n}.")
                return
            if v['country'].get().strip() not in self.countries:
                messagebox.showerror("Validation Error", f"Select a valid country for Visitor {n}.")
                return
            if not v['gender'].get().strip():
                messagebox.showerror("Validation Error", f"Select gender for Visitor {n}.")
                return
            if "No File Selected" in v['photo'].cget("text"):
                messagebox.showerror("Validation Error", f"Upload photo for Visitor {n}.")
                return

        if not self.purpose.get():
            messagebox.showerror("Validation Error", "Purpose is required.")
            return
        if not self.region.get():
            messagebox.showerror("Validation Error", "Trekking Region is required.")
            return
        if not self.entry_point.get() or not self.exit_point.get():
            messagebox.showerror("Validation Error", "Entry Point and Exit Point are required.")
            return

        self.save_to_database()

    # ══════════════════════════════════════
    # SAVE → DB → PDF
    # ══════════════════════════════════════

    def save_to_database(self):
        import datetime as dt

        # Collect Section B
        purpose    = self.purpose.get().strip()
        region     = self.region.get().strip()
        entry_pt   = self.entry_point.get().strip()
        exit_pt    = self.exit_point.get().strip()
        start_d    = self.start_date.get()
        end_d      = self.end_date.get()

        # Collect Section C
        guide_trained_val = 1 if self.guide_trained.get() == "Yes" else 0
        # Parse DOB for applicant (if present)
        dob = None
        try:
            dob = parse_dob(self.dob_entry.get()) if hasattr(self, 'dob_entry') else None
        except Exception:
            dob = None

        if getattr(self, 'dob_entry', None) and dob is None:
            messagebox.showerror("Invalid Date", "Date of Birth must be DD/MM/YYYY\nExample: 15/08/1990")
            return
        generated_tickets = []

        for idx, visitor in enumerate(self.visitor_fields_data):
            first_name  = visitor['first_name'].get().strip()
            mid_name    = visitor['mid_name'].get().strip() or None
            last_name   = visitor['last_name'].get().strip()
            full_name   = f"{first_name} {mid_name} {last_name}".strip() if mid_name \
                          else f"{first_name} {last_name}".strip()
            passport    = visitor['passport'].get().strip().upper()
            country     = visitor['country'].get().strip()
            gender      = visitor['gender'].get().strip()
            dob_raw     = visitor['dob'].get().strip()
            dob         = dob_raw if dob_raw != "MM/DD/YYYY" else None
            occupation  = visitor['occupation'].get().strip()
            photo_src   = visitor['photo'].cget("text")

            # Copy photo to PHOTOS_DIR temporarily
            saved_photo = None
            if photo_src and photo_src != "No File Selected" and os.path.exists(photo_src):
                ext      = os.path.splitext(photo_src)[1]
                tmp_path = os.path.join(PHOTOS_DIR, f"temp_v{idx}{ext}")
                try:
                    shutil.copy2(photo_src, tmp_path)
                    saved_photo = tmp_path
                except Exception as e:
                    print(f"[PHOTO] Copy failed: {e}")

            # Build the data dict — field names match save_tourist() exactly
            tourist_data = {
                # Personal
                "first_name":       first_name,
                "mid_name":         mid_name,
                "last_name":        last_name,
                "dob":              dob,
                "gender":           gender,         # Male/Female/Other → mapped to M/F/O in save_tourist
                # Country & nationality
                "country":          country,        # → resolved to country_id in save_tourist
                # Occupation
                "occupation":       occupation,     # → resolved to occupation_id
                # Visit
                "purpose":          purpose,        # Trekking/Tourism/Research → purpose_id
                "region":           region,         # → region_id
                "entry_point":      entry_pt,       # → entry_post_id
                "exit_point":       exit_pt,        # → exit_post_id
                # Documents
                "passport_number":  passport,
                "photo_path":       saved_photo,
                # Dates
                "entry_date":       start_d,
                "expiry_date":      end_d,
                # Guide
                "guide_name":       self.guide_name.get().strip() or None,
                "guide_contact":    self.guide_contact.get().strip() or None,
                "guide_total":      self.guide_total.get().strip() or None,
                "guide_trained":    guide_trained_val,
                # Porter
                "porter_name":      self.porter_name.get().strip() or None,
                "porter_contact":   self.porter_contact.get().strip() or None,
                "porter_total":     self.porter_total.get().strip() or None,
                # Meta
                "created_by":       self.officer,
                "fiscal_year":      f"{dt.date.today().year}/{dt.date.today().year + 1 - 2000:02d}",
            }

            # Save to MySQL
            ticket_number = save_tourist(tourist_data)

            if not ticket_number:
                messagebox.showerror("Database Error",
                    f"Could not save Visitor {idx+1} ({full_name}).")
                continue

            # Rename photo file to match ticket_number
            if saved_photo and os.path.exists(saved_photo):
                ext      = os.path.splitext(saved_photo)[1]
                new_path = os.path.join(PHOTOS_DIR, f"{ticket_number}{ext}")
                os.rename(saved_photo, new_path)
                tourist_data["photo_path"] = new_path
                from database.local_db import run_query
                run_query(
                    "UPDATE tourists SET photo_path=%s WHERE ticket_number=%s",
                    (new_path, ticket_number)
                )

            # Generate QR code
            generate_qr(ticket_number)

            # Build full data dict for PDF
            tourist_data["ticket_number"] = ticket_number
            tourist_data["full_name"]     = full_name
            tourist_data["nationality"]   = country
            tourist_data["created_at"]    = dt.datetime.now()
            tourist_data["destination"]   = region
            tourist_data["sub_area"]      = region
            tourist_data["permit_code"]   = ticket_number
            tourist_data["permit_ref"]    = ticket_number
            tourist_data["permit_cost"]   = "NPR. 1000 (13% VAT included)"
            tourist_data["el_code"]       = ""
            tourist_data["serial_code"]   = ""
            tourist_data["agency"]        = f"{self.officer}  |  {self.checkpost}"

            try:
                pdf_path = generate_ticket_pdf(tourist_data, scan_history=[])
                generated_tickets.append((ticket_number, full_name, pdf_path))
                print(f"[TICKET] {ticket_number} — {full_name}")
            except Exception as e:
                print(f"[PDF ERROR] {full_name}: {e}")

        if not generated_tickets:
            messagebox.showerror("Failed", "No tickets were created.")
            return

        summary = "\n".join(f"• {tn}  —  {name}" for tn, name, _ in generated_tickets)
        messagebox.showinfo("Tickets Created!",
            f"{len(generated_tickets)} ticket(s) saved:\n\n{summary}")

        # Open first PDF
        first_pdf = generated_tickets[0][2]
        try:
            os.startfile(first_pdf)
        except Exception:
            subprocess.Popen(["start", first_pdf], shell=True)


if __name__ == "__main__":
    root = tk.Tk()
    app  = TicketUI(root)
    root.mainloop()