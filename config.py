# config.py
import os

# ── Base paths ────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR    = os.path.join(BASE_DIR, "assets")
PHOTOS_DIR    = os.path.join(BASE_DIR, "photos")
TICKETS_DIR   = os.path.join(BASE_DIR, "tickets")
QR_DIR        = os.path.join(BASE_DIR, "qrcodes")

# ── Nepal logo path ───────────────────────
NEPAL_LOGO    = os.path.join(ASSETS_DIR, "logo.png")

# ── Create folders if they don't exist ────
for folder in [ASSETS_DIR, PHOTOS_DIR, TICKETS_DIR, QR_DIR]:
    os.makedirs(folder, exist_ok=True)

# ── Local MySQL ───────────────────────────
LOCAL_DB = {
    "host":     "localhost",
    "port":     3306,
    "user":     "ticket_app",
    "password": "Nepal@2026",
    "database": "nepal_ticketing",
}

# ── Online MySQL (fill later) ─────────────
ONLINE_DB = {
    "host":     None,
    "port":     3306,
    "user":     "ticket_app",
    "password": "Nepal@2026",
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
UI_ONLY_MODE=False

# ── Debug print (remove later) ────────────
if __name__ == "__main__":
    print("BASE_DIR    :", BASE_DIR)
    print("QR_DIR      :", QR_DIR)
    print("TICKETS_DIR :", TICKETS_DIR)
    print("PHOTOS_DIR  :", PHOTOS_DIR)
    print("NEPAL_LOGO  :", NEPAL_LOGO)
    print("Folders exist:")
    for folder in [ASSETS_DIR, PHOTOS_DIR, TICKETS_DIR, QR_DIR]:
        print(f"  {folder} → exists={os.path.exists(folder)}")
# USE nepal_ticketing;

# -- Add officers with passwords
# -- Password is stored as a hash (never plain text)
# INSERT IGNORE INTO officers (username, password_hash, full_name, checkpost) VALUES
# ('admin',   SHA2('admin123',   256), 'System Admin',      'Birgunj'),
# ('ram',     SHA2('ram123',     256), 'Ram Sharma',        'Birgunj'),
# ('sita',    SHA2('sita123',    256), 'Sita Thapa',        'Bhairahawa'),
# ('hari',    SHA2('hari123',    256), 'Hari Bahadur',      'Kakarbhitta'),
# ('sujan',   SHA2('sujan123',   256), 'Sujan',             'Mahendranagar');
# ('krishna', SHA2('krishna123', 256), 'Krishna Pradhan',   'Dhangadhi'),