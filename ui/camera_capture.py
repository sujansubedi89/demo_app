# ui/camera_capture.py
# ============================================
# Live camera window for capturing tourist photo
# ============================================

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import time

from config import PHOTOS_DIR


class CameraCapture:
    def __init__(self, root, callback=None):
        """
        callback = function(saved_path) called when photo is taken.
        If user cancels, callback is called with None.
        """
        self.root     = root
        self.callback = callback
        self.cap      = None
        self.running  = False
        self.current_frame = None    # holds latest camera frame
        self.countdown_active = False

        self.root.title("Take Tourist Photo")
        self.root.geometry("620x540")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        # Center it
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - 310
        y = (self.root.winfo_screenheight() // 2) - 270
        self.root.geometry(f"620x540+{x}+{y}")

        self.root.protocol("WM_DELETE_WINDOW", self._cancel)

        self._build_ui()
        self.root.after(300, self._start_camera)

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#C0392B", height=45)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="📸  LIVE PHOTO CAPTURE",
            font=("Helvetica", 13, "bold"),
            bg="#C0392B", fg="white"
        ).pack(side="left", padx=20, pady=10)

        # Camera feed
        self.camera_label = tk.Label(
            self.root,
            text="Starting camera...",
            bg="#0D1117", fg="#30A14E",
            font=("Helvetica", 11),
            width=60, height=16
        )
        self.camera_label.pack(padx=15, pady=10)

        # Guide text
        self.guide_label = tk.Label(
            self.root,
            text="Position tourist's face in the center",
            font=("Helvetica", 10),
            bg="#1a1a2e", fg="#AEB6BF"
        )
        self.guide_label.pack()

        # Countdown label (shown during countdown)
        self.countdown_label = tk.Label(
            self.root,
            text="",
            font=("Helvetica", 32, "bold"),
            bg="#1a1a2e", fg="#F39C12"
        )
        self.countdown_label.pack(pady=2)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=8)

        self.capture_btn = tk.Button(
            btn_frame,
            text="📸  Capture Photo",
            font=("Helvetica", 12, "bold"),
            bg="#1E8449", fg="white",
            activebackground="#145A32",
            activeforeground="white",
            relief="flat", cursor="hand2",
            padx=25, pady=10,
            command=self._start_countdown
        )
        self.capture_btn.pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="✕  Cancel",
            font=("Helvetica", 11),
            bg="#922B21", fg="white",
            relief="flat", cursor="hand2",
            padx=20, pady=10,
            command=self._cancel
        ).pack(side="left", padx=10)

    def _start_camera(self):
        """Opens the webcam."""
        try:
            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                self.camera_label.configure(
                    text="No camera found.\nConnect a webcam and try again.",
                    fg="#E74C3C"
                )
                self.capture_btn.configure(state="disabled")
                return

            self.running = True
            self._update_frame()

        except Exception as e:
            self.camera_label.configure(
                text=f"Camera error:\n{e}",
                fg="#E74C3C"
            )

    def _update_frame(self):
        """Reads camera frame and updates UI — runs every 30ms."""
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self._update_frame)
            return

        # Mirror the frame so it feels like a selfie camera
        frame = cv2.flip(frame, 1)

        # Draw face guide oval on frame
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        cv2.ellipse(
            frame,
            (cx, cy),
            (int(w * 0.18), int(h * 0.32)),
            0, 0, 360,
            (0, 255, 100), 2
        )

        # Store for capture
        self.current_frame = frame.copy()

        # Convert to Tkinter image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((580, 340), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        self.camera_label.configure(image=photo, text="")
        self.camera_label.image = photo

        self.root.after(30, self._update_frame)

    def _start_countdown(self):
        """3 second countdown before capture."""
        if self.countdown_active:
            return

        self.countdown_active = True
        self.capture_btn.configure(state="disabled")
        self.guide_label.configure(
            text="Hold still...",
            fg="#F39C12"
        )
        self._countdown(3)

    def _countdown(self, count):
        """Recursive countdown 3 → 2 → 1 → capture."""
        if count > 0:
            self.countdown_label.configure(text=str(count))
            self.root.after(1000, lambda: self._countdown(count - 1))
        else:
            self.countdown_label.configure(text="✓")
            self.root.after(200, self._capture_photo)

    def _capture_photo(self):
        """Saves the current frame as a JPEG file."""
        if self.current_frame is None:
            messagebox.showerror("Error", "No frame captured.")
            self._reset_ui()
            return

        try:
            os.makedirs(PHOTOS_DIR, exist_ok=True)

            # Save with timestamp as temp name
            # Will be renamed to ticket number after ticket is saved
            timestamp = int(time.time())
            filename  = f"capture_{timestamp}.jpg"
            save_path = os.path.join(PHOTOS_DIR, filename)

            # Crop to portrait ratio (centered)
            frame = self.current_frame
            h, w  = frame.shape[:2]

            # Crop center portrait
            target_w = int(h * 0.6)
            x_start  = max(0, (w - target_w) // 2)
            cropped  = frame[:, x_start:x_start + target_w]

            cv2.imwrite(save_path, cropped)
            print(f"[CAMERA] Photo saved: {save_path}")

            # Show success
            self.countdown_label.configure(text="✅", fg="#1E8449")
            self.guide_label.configure(
                text="Photo captured successfully!",
                fg="#1E8449"
            )

            # Close after short delay and call callback
            self.root.after(800, lambda: self._finish(save_path))

        except Exception as e:
            messagebox.showerror("Capture Error", f"Could not save photo:\n{e}")
            self._reset_ui()

    def _reset_ui(self):
        """Resets UI after failed capture."""
        self.countdown_active = False
        self.countdown_label.configure(text="")
        self.guide_label.configure(
            text="Position tourist's face in the center",
            fg="#AEB6BF"
        )
        self.capture_btn.configure(state="normal")

    def _finish(self, saved_path):
        """Closes camera and returns photo path."""
        self._stop_camera()
        if self.callback:
            self.callback(saved_path)
        self.root.destroy()

    def _cancel(self):
        """User pressed cancel."""
        self._stop_camera()
        if self.callback:
            self.callback(None)
        self.root.destroy()

    def _stop_camera(self):
        """Releases webcam."""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None