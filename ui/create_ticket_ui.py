# ui/create_ticket_ui.py
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
from PIL import Image, ImageTk
import shutil

from config import (
    VISA_TYPES, VEHICLE_TYPES,
    TICKET_VALIDITY_DAYS, PHOTOS_DIR
)
from modules.ticket_creator import save_tourist
from modules.pdf_generator  import generate_ticket_pdf
from modules.qr_generator   import generate_qr


class CreateTicketWindow:
    def __init__(self, root, officer_name, checkpost, on_success=None):
        self.root       = root
        self.officer    = officer_name
        self.checkpost  = checkpost
        self.on_success = on_success
        self.photo_path = None
        self._scroll_binding = None   # track scroll binding so we can remove it

        self.root.title("Create New Tourist Ticket")
        self.root.geometry("750x700")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(False, False)

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - 375
        y = (self.root.winfo_screenheight() // 2) - 350
        self.root.geometry(f"750x700+{x}+{y}")

        self._build_ui()

        # Clean up scroll binding when window closes
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Unbind mouse wheel before destroying to prevent crash."""
        try:
            self.root.unbind_all("<MouseWheel>")
        except:
            pass
        self.root.destroy()

    def _build_ui(self):
        # ── Header ────────────────────────
        header = tk.Frame(self.root, bg="#C0392B", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="NEW TOURIST TICKET",
            font=("Helvetica", 14, "bold"),
            bg="#C0392B", fg="white"
        ).pack(side="left", padx=20, pady=12)

        tk.Label(
            header,
            text=f"Officer: {self.officer}  |  {self.checkpost}",
            font=("Helvetica", 9),
            bg="#C0392B", fg="#FADBD8"
        ).pack(side="right", padx=20)

        # ── Scrollable form ───────────────
        canvas_frame = tk.Frame(self.root, bg="#f0f0f0")
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.form_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.form_frame, anchor="nw"
        )

        self.form_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>",     self._on_canvas_configure)

        # Bind scroll ONLY to this canvas (not global)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.form_frame.bind("<MouseWheel>", self._on_mousewheel)

        self._build_form()

        # ── Bottom buttons ────────────────
        btn_bar = tk.Frame(self.root, bg="#2C3E50", height=55)
        btn_bar.pack(fill="x", side="bottom")
        btn_bar.pack_propagate(False)

        tk.Button(
            btn_bar,
            text="✕  Cancel",
            font=("Helvetica", 10),
            bg="#922B21", fg="white",
            relief="flat", cursor="hand2",
            padx=20, pady=8,
            command=self._on_close
        ).pack(side="right", padx=10, pady=10)

        tk.Button(
            btn_bar,
            text="🖨  Save & Print Ticket",
            font=("Helvetica", 11, "bold"),
            bg="#1E8449", fg="white",
            activebackground="#145A32",
            activeforeground="white",
            relief="flat", cursor="hand2",
            padx=20, pady=8,
            command=self._save_and_print
        ).pack(side="right", padx=5, pady=10)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Scroll only if canvas still exists."""
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except:
            pass

    def _section_label(self, text):
        frame = tk.Frame(self.form_frame, bg="#2C3E50")
        frame.pack(fill="x", padx=20, pady=(15, 5))
        tk.Label(
            frame, text=f"  {text}",
            font=("Helvetica", 10, "bold"),
            bg="#2C3E50", fg="white", pady=5
        ).pack(side="left")

    def _make_row(self, label, widget_builder, required=False):
        frame = tk.Frame(self.form_frame, bg="#f0f0f0")
        frame.pack(fill="x", padx=20, pady=4)

        tk.Label(
            frame,
            text=f"{'*' if required else ' '} {label}",
            font=("Helvetica", 10),
            bg="#f0f0f0", fg="#2C3E50",
            width=18, anchor="w"
        ).pack(side="left")

        widget = widget_builder(frame)
        widget.pack(side="left", fill="x", expand=True, ipady=4)
        return widget

    def _make_entry(self, parent, placeholder=""):
        e = tk.Entry(parent, font=("Helvetica", 10), relief="solid", bd=1, bg="white")
        if placeholder:
            e.insert(0, placeholder)
            e.configure(fg="gray")
            e.bind("<FocusIn>",  lambda ev: self._clear_ph(ev, placeholder))
            e.bind("<FocusOut>", lambda ev: self._add_ph(ev, placeholder))
        return e

    def _clear_ph(self, event, placeholder):
        if event.widget.get() == placeholder:
            event.widget.delete(0, tk.END)
            event.widget.configure(fg="black")

    def _add_ph(self, event, placeholder):
        if not event.widget.get().strip():
            event.widget.insert(0, placeholder)
            event.widget.configure(fg="gray")

    def _make_dropdown(self, parent, options):
        var = tk.StringVar(value=options[0])
        dd  = ttk.Combobox(
            parent, textvariable=var,
            values=options, state="readonly",
            font=("Helvetica", 10)
        )
        dd.var = var
        return dd

    def _build_form(self):
        tk.Frame(self.form_frame, bg="#f0f0f0", height=10).pack()

        # ── Personal Info ──────────────────
        self._section_label("👤  Personal Information")
        self.f_name        = self._make_row("Full Name",       lambda p: self._make_entry(p, "e.g. John Michael Doe"), required=True)
        self.f_passport    = self._make_row("Passport Number", lambda p: self._make_entry(p, "e.g. A12345678"),        required=True)
        self.f_nationality = self._make_row("Nationality",     lambda p: self._make_entry(p, "e.g. United States"),    required=True)

        # ── Visa & Entry ───────────────────
        self._section_label("📄  Visa & Entry Details")
        self.f_visa_type   = self._make_row("Visa Type",   lambda p: self._make_dropdown(p, VISA_TYPES))
        self.f_entry_date  = self._make_row("Entry Date",  lambda p: self._make_entry(p, date.today().strftime("%Y-%m-%d")), required=True)
        self.f_expiry_date = self._make_row("Expiry Date", lambda p: self._make_entry(p, (date.today() + timedelta(days=TICKET_VALIDITY_DAYS)).strftime("%Y-%m-%d")), required=True)
        self.f_entry_date.bind("<FocusOut>", self._auto_expiry)

        # ── Vehicle ────────────────────────
        self._section_label("🚗  Vehicle Information")
        self.f_vehicle_type   = self._make_row("Vehicle Type",   lambda p: self._make_dropdown(p, VEHICLE_TYPES))
        self.f_vehicle_number = self._make_row("Vehicle Number", lambda p: self._make_entry(p, "e.g. BA 1 KHA 2345"))

        # ── Photo ──────────────────────────
        self._section_label("📷  Tourist Photo")

        photo_frame = tk.Frame(self.form_frame, bg="#f0f0f0")
        photo_frame.pack(fill="x", padx=20, pady=8)

        self.photo_label = tk.Label(
            photo_frame,
            text="No photo\nselected",
            font=("Helvetica", 9),
            bg="#D5D8DC", fg="#7F8C8D",
            width=12, height=6,
            relief="solid", bd=1
        )
        self.photo_label.pack(side="left")

        btn_col = tk.Frame(photo_frame, bg="#f0f0f0")
        btn_col.pack(side="left", padx=15)

        tk.Button(
            btn_col,
            text="📂  Choose Photo File",
            font=("Helvetica", 9),
            bg="#2980B9", fg="white",
            activebackground="#1A6FA0",
            activeforeground="white",
            relief="flat", cursor="hand2",
            padx=10, pady=6,
            command=self._choose_photo
        ).pack(anchor="w", pady=3)

        tk.Label(
            btn_col,
            text="JPG or PNG  |  passport-size recommended",
            font=("Helvetica", 8),
            bg="#f0f0f0", fg="#7F8C8D"
        ).pack(anchor="w")

        # ── Officer ────────────────────────
        self._section_label("👮  Officer Details")

        row = tk.Frame(self.form_frame, bg="#f0f0f0")
        row.pack(fill="x", padx=20, pady=4)

        tk.Label(row, text="   Issuing Officer:", font=("Helvetica", 10),
                 bg="#f0f0f0", fg="#2C3E50", width=18, anchor="w").pack(side="left")
        tk.Label(row, text=self.officer, font=("Helvetica", 10, "bold"),
                 bg="#f0f0f0", fg="#1E8449").pack(side="left")

        tk.Frame(self.form_frame, bg="#f0f0f0", height=20).pack()

    def _auto_expiry(self, event=None):
        try:
            entry_str = self.f_entry_date.get().strip()
            entry_dt  = date.fromisoformat(entry_str)
            expiry_dt = entry_dt + timedelta(days=TICKET_VALIDITY_DAYS)
            self.f_expiry_date.delete(0, tk.END)
            self.f_expiry_date.insert(0, expiry_dt.strftime("%Y-%m-%d"))
            self.f_expiry_date.configure(fg="black")
        except:
            pass

    def _choose_photo(self):
        path = filedialog.askopenfilename(
            title="Select Tourist Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if not path:
            return

        try:
            img = Image.open(path)
            img.thumbnail((90, 110))
            photo = ImageTk.PhotoImage(img)
            self.photo_label.configure(image=photo, text="")
            self.photo_label.image = photo
            self.photo_path = path
            print(f"[PHOTO] Selected: {path}")
        except Exception as e:
            messagebox.showerror("Photo Error", f"Could not load photo:\n{e}")

    def _get_value(self, widget, placeholder=""):
        """Gets Entry value, returns empty string if still placeholder."""
        val = widget.get().strip()
        return "" if val == placeholder else val

    def _validate(self):
        errors = []

        if not self._get_value(self.f_name, "e.g. John Michael Doe"):
            errors.append("Full Name is required.")
        if not self._get_value(self.f_passport, "e.g. A12345678"):
            errors.append("Passport Number is required.")
        if not self._get_value(self.f_nationality, "e.g. United States"):
            errors.append("Nationality is required.")

        try:
            date.fromisoformat(self._get_value(self.f_entry_date))
        except:
            errors.append("Entry Date must be YYYY-MM-DD format.")

        try:
            date.fromisoformat(self._get_value(self.f_expiry_date))
        except:
            errors.append("Expiry Date must be YYYY-MM-DD format.")

        if errors:
            messagebox.showerror(
                "Missing Information",
                "Please fix:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
            return False
        return True

    def _save_and_print(self):
        if not self._validate():
            return

        # Save photo to photos/ folder with temp name
        saved_photo_path = None
        if self.photo_path:
            try:
                ext = os.path.splitext(self.photo_path)[1]
                dst = os.path.join(PHOTOS_DIR, f"temp_photo{ext}")
                shutil.copy2(self.photo_path, dst)
                saved_photo_path = dst
            except Exception as e:
                messagebox.showwarning("Photo Warning", f"Could not copy photo:\n{e}\nContinuing without photo.")

        # Build data dict
        tourist_data = {
            "full_name":       self._get_value(self.f_name,           "e.g. John Michael Doe"),
            "passport_number": self._get_value(self.f_passport,       "e.g. A12345678"),
            "nationality":     self._get_value(self.f_nationality,    "e.g. United States"),
            "visa_type":       self.f_visa_type.var.get(),
            "vehicle_type":    self.f_vehicle_type.var.get(),
            "vehicle_number":  self._get_value(self.f_vehicle_number, "e.g. BA 1 KHA 2345"),
            "entry_date":      self._get_value(self.f_entry_date),
            "expiry_date":     self._get_value(self.f_expiry_date),
            "photo_path":      saved_photo_path,
            "created_by":      self.officer,
        }

        # Save to DB — this now correctly generates ticket_number inside
        ticket_number = save_tourist(tourist_data)

        if not ticket_number:
            messagebox.showerror("Error", "Failed to save to database.\nCheck terminal for details.")
            return

        # Rename photo to ticket number
        if saved_photo_path and os.path.exists(saved_photo_path):
            ext      = os.path.splitext(saved_photo_path)[1]
            new_path = os.path.join(PHOTOS_DIR, f"{ticket_number}{ext}")
            os.rename(saved_photo_path, new_path)
            tourist_data["photo_path"] = new_path

            from database.local_db import run_query
            run_query(
                "UPDATE tourists SET photo_path=%s WHERE ticket_number=%s",
                (new_path, ticket_number)
            )

        # Add fields needed by PDF
        import datetime
        tourist_data["ticket_number"] = ticket_number
        tourist_data["created_at"]    = datetime.datetime.now()

        # Generate PDF
        try:
            pdf_path = generate_ticket_pdf(tourist_data, scan_history=[])
        except Exception as e:
            messagebox.showerror("PDF Error", f"Ticket saved but PDF failed:\n{e}")
            return

        messagebox.showinfo(
            "✅ Ticket Created!",
            f"Ticket Number: {ticket_number}\n"
            f"Tourist: {tourist_data['full_name']}\n\n"
            f"PDF saved to:\n{pdf_path}"
        )

        # Open PDF
        try:
            os.startfile(pdf_path)
        except:
            import subprocess
            subprocess.Popen(["start", pdf_path], shell=True)

        if self.on_success:
            self.on_success()

        self._on_close()