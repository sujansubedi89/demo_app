# config.example.py
# ============================================
# COPY THIS FILE TO config.py
# Then fill in your own database credentials
# Command: copy config.example.py config.py
# ============================================

import os

# ── Base paths ────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
PHOTOS_DIR  = os.path.join(BASE_DIR, "photos")
TICKETS_DIR = os.path.join(BASE_DIR, "tickets")
QR_DIR      = os.path.join(BASE_DIR, "qrcodes")
NEPAL_LOGO  = os.path.join(ASSETS_DIR, "nepal_logo.jpg")

# Create folders automatically
for folder in [ASSETS_DIR, PHOTOS_DIR, TICKETS_DIR, QR_DIR]:
    os.makedirs(folder, exist_ok=True)

# ── Local MySQL — FILL THESE IN ───────────
LOCAL_DB = {
    "host":     "localhost",
    "port":     3306,
    "user":     "ticket_app",       # your MySQL username
    "password": "YOUR_PASSWORD",    # ← change this
    "database": "nepal_ticketing",
}

# ── Online MySQL (optional) ───────────────
ONLINE_DB = {
    "host":     None,               # e.g. "192.168.1.100"
    "port":     3306,
    "user":     "ticket_app",
    "password": "YOUR_PASSWORD",    # ← change this
    "database": "nepal_ticketing",
}

# ── Checkposts ────────────────────────────
CHECKPOSTS = [
    "Birgunj",
    "Bhairahawa",
    "Kakarbhitta",
    "Dhangadhi",
    "Mahendranagar",
]

# ── Visa types ────────────────────────────
VISA_TYPES = [
    "Tourist",
    "Business",
    "Transit",
    "Pilgrimage",
    "Student",
]

# ── Vehicle types ─────────────────────────
VEHICLE_TYPES = [
    "None",
    "Car",
    "Motorcycle",
    "Bus",
    "Truck",
    "Other",
]

# ── Ticket settings ───────────────────────
TICKET_PREFIX        = "NPL"
TICKET_VALIDITY_DAYS = 30

# ── App info ──────────────────────────────
APP_NAME    = "Nepal Tourist Ticketing System"
APP_VERSION = "1.0"