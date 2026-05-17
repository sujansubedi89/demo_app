# ui/scanner_ui.py
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from database.local_db import run_query


class ScannerWindow:
    def __init__(self, root, officer_name, checkpost):
        self.root      = root
        self.officer   = officer_name
        self.checkpost = checkpost
        self.last_scan = None   # prevent double-scanning same ticket

        self.root.title(f"QR Scanner — {checkpost}")
        self.root.geometry("600x500")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1A5276", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"📷  QR SCANNER  —  {self.checkpost.upper()}",
            font=("Helvetica", 13, "bold"),
            bg="#1A5276", fg="white"
        ).pack(side="left", padx=20, pady=12)

        # Camera feed area
        self.camera_label = tk.Label(
            self.root,
            text="Camera loading...",
            bg="#0D1117", fg="#30A14E",
            font=("Courier", 11),
            width=50, height=14
        )
        self.camera_label.pack(padx=20, pady=15)

        # Status display
        self.status_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.status_frame.pack(fill="x", padx=20)

        self.status_var = tk.StringVar(value="Point camera at QR code...")
        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=("Helvetica", 11),
            bg="#1a1a2e", fg="#85C1E9",
            wraplength=550
        )
        self.status_label.pack(pady=8)

        # Result box (shows tourist details after scan)
        self.result_frame = tk.Frame(self.root, bg="#0D1117", pady=10)
        self.result_frame.pack(fill="x", padx=20, pady=5)

        self.result_var = tk.StringVar(value="")
        tk.Label(
            self.result_frame,
            textvariable=self.result_var,
            font=("Courier", 10),
            bg="#0D1117", fg="#30A14E",
            justify="left",
            wraplength=540
        ).pack(padx=15, pady=5)

        # Manual entry option
        manual_frame = tk.Frame(self.root, bg="#1a1a2e")
        manual_frame.pack(fill="x", padx=20, pady=8)

        tk.Label(
            manual_frame,
            text="Or enter ticket number manually:",
            font=("Helvetica", 9),
            bg="#1a1a2e", fg="#AEB6BF"
        ).pack(side="left")

        self.manual_entry = tk.Entry(
            manual_frame,
            font=("Helvetica", 10),
            width=18, relief="solid"
        )
        self.manual_entry.pack(side="left", padx=8, ipady=3)

        tk.Button(
            manual_frame,
            text="Verify",
            font=("Helvetica", 9, "bold"),
            bg="#1A5276", fg="white",
            relief="flat", cursor="hand2",
            padx=10,
            command=self._manual_verify
        ).pack(side="left")

        # Close button
        tk.Button(
            self.root,
            text="Close Scanner",
            font=("Helvetica", 10),
            bg="#922B21", fg="white",
            relief="flat", cursor="hand2",
            padx=15, pady=6,
            command=self._close
        ).pack(pady=10)

        # Start camera
        self.running = True
        self.cap     = None
        self.root.after(500, self._start_camera)

    def _start_camera(self):
        """Starts the webcam feed."""
        try:
            import cv2
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.status_var.set("No camera found. Use manual entry below.")
                return
            self._scan_loop()
        except Exception as e:
            self.status_var.set(f"Camera error: {e}\nUse manual entry below.")

    def _scan_loop(self):
        """Continuously reads camera frames and looks for QR codes."""
        if not self.running:
            return

        try:
            import cv2
            from pyzbar import pyzbar
            from PIL import Image, ImageTk

            ret, frame = self.cap.read()
            if not ret:
                self.root.after(100, self._scan_loop)
                return

            # Look for QR codes in the frame
            decoded = pyzbar.decode(frame)

            for obj in decoded:
                ticket_number = obj.data.decode("utf-8").strip()

                # Only process if different from last scan (avoid repeated beeps)
                if ticket_number != self.last_scan:
                    self.last_scan = ticket_number
                    self._process_scan(ticket_number)

            # Show camera feed in UI
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((560, 280))
            photo = ImageTk.PhotoImage(img)
            self.camera_label.configure(image=photo, text="")
            self.camera_label.image = photo

        except Exception as e:
            self.status_var.set(f"Scan error: {e}")

        # Run again in 50ms (20 fps)
        self.root.after(50, self._scan_loop)

    def _process_scan(self, ticket_number):
        """Looks up the ticket in DB and logs the scan."""
        # Look up tourist
        rows = run_query(
            "SELECT * FROM tourists WHERE ticket_number = %s",
            (ticket_number,),
            fetch=True
        )

        if not rows:
            self._show_result("FAIL", ticket_number, None)
            self._log_scan(ticket_number, "FAIL")
            return

        tourist = rows[0]

        # Check if ticket is expired
        today = __import__("datetime").date.today()
        expiry = tourist["expiry_date"]
        if hasattr(expiry, "date"):
            expiry = expiry.date()

        if today > expiry:
            self._show_result("EXPIRED", ticket_number, tourist)
            self._log_scan(ticket_number, "FAIL")
            return

        # All good
        self._show_result("PASS", ticket_number, tourist)
        self._log_scan(ticket_number, "PASS")

    def _log_scan(self, ticket_number, status):
        """Saves the scan to checkpost_logs table."""
        run_query(
            """INSERT INTO checkpost_logs
               (ticket_number, checkpost_name, officer_name, status)
               VALUES (%s, %s, %s, %s)""",
            (ticket_number, self.checkpost, self.officer, status)
        )

    def _show_result(self, status, ticket_number, tourist):
        """Updates the UI to show PASS or FAIL result."""
        if status == "PASS":
            color = "#27AE60"
            icon  = "✅  PASS"
            self.status_label.configure(fg=color)
            info  = (
                f"Ticket:      {ticket_number}\n"
                f"Name:        {tourist['full_name']}\n"
                f"Nationality: {tourist['nationality']}\n"
                f"Passport:    {tourist['passport_number']}\n"
                f"Valid Until: {tourist['expiry_date']}\n"
                f"Scanned at:  {self.checkpost}  —  "
                f"{datetime.now().strftime('%H:%M:%S')}"
            )
        elif status == "EXPIRED":
            color = "#F39C12"
            icon  = "⚠️  EXPIRED"
            self.status_label.configure(fg=color)
            info  = (
                f"Ticket:      {ticket_number}\n"
                f"Name:        {tourist['full_name']}\n"
                f"STATUS:      TICKET EXPIRED\n"
                f"Expired on:  {tourist['expiry_date']}"
            )
        else:
            color = "#E74C3C"
            icon  = "❌  FAIL — Ticket not found"
            self.status_label.configure(fg=color)
            info  = f"Ticket number not found in system:\n{ticket_number}"

        self.status_var.set(icon)
        self.result_var.set(info)

    def _manual_verify(self):
        """Handles manual ticket number entry."""
        ticket_number = self.manual_entry.get().strip().upper()
        if not ticket_number:
            return
        self.last_scan = None   # allow re-scan
        self._process_scan(ticket_number)
        self.manual_entry.delete(0, tk.END)

    def _close(self):
        self.running = False
        if self.cap:
            import cv2
            self.cap.release()
        self.root.destroy()