# check_data.py
# Run this anytime to see what's saved in DB and folders
# Usage: python check_data.py

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from database.local_db import run_query
from config import QR_DIR, TICKETS_DIR, PHOTOS_DIR


print("=" * 55)
print("   NEPAL TICKETING — DATA CHECK")
print("=" * 55)

# ── Tourists in database ──────────────────
tourists = run_query(
    "SELECT ticket_number, full_name, nationality, entry_date, synced FROM tourists ORDER BY id DESC",
    fetch=True
) or []

print(f"\n📋 TOURISTS IN DATABASE ({len(tourists)} total)\n")

if tourists:
    for t in tourists:
        synced = "✅ synced" if t["synced"] else "⏳ not synced"
        print(f"  {t['ticket_number']}  |  {t['full_name']}")
        print(f"    Nationality : {t['nationality']}")
        print(f"    Entry Date  : {t['entry_date']}")
        print(f"    Sync Status : {synced}")
        print()
else:
    print("  No tourists found in database yet.\n")

# ── QR codes in folder ────────────────────
qr_files = [f for f in os.listdir(QR_DIR) if f.endswith(".png")] if os.path.exists(QR_DIR) else []
print(f"📷 QR CODES IN FOLDER ({len(qr_files)} files)")
print(f"   Location: {QR_DIR}\n")
if qr_files:
    for f in qr_files:
        size = os.path.getsize(os.path.join(QR_DIR, f))
        print(f"  {f}  ({size} bytes)")
else:
    print("  No QR codes found.")
print()

# ── PDF tickets in folder ─────────────────
pdf_files = [f for f in os.listdir(TICKETS_DIR) if f.endswith(".pdf")] if os.path.exists(TICKETS_DIR) else []
print(f"🎫 PDF TICKETS IN FOLDER ({len(pdf_files)} files)")
print(f"   Location: {TICKETS_DIR}\n")
if pdf_files:
    for f in pdf_files:
        size = os.path.getsize(os.path.join(TICKETS_DIR, f))
        print(f"  {f}  ({size} bytes)")
else:
    print("  No PDF tickets found.")
print()

# ── Photos in folder ──────────────────────
photo_files = [f for f in os.listdir(PHOTOS_DIR) if f.lower().endswith((".jpg",".jpeg",".png"))] if os.path.exists(PHOTOS_DIR) else []
print(f"🖼  PHOTOS IN FOLDER ({len(photo_files)} files)")
print(f"   Location: {PHOTOS_DIR}\n")
if photo_files:
    for f in photo_files:
        size = os.path.getsize(os.path.join(PHOTOS_DIR, f))
        print(f"  {f}  ({size} bytes)")
else:
    print("  No photos found.")
print()

# ── Checkpost scans in database ───────────
scans = run_query(
    "SELECT ticket_number, checkpost_name, officer_name, scan_time, status FROM checkpost_logs ORDER BY scan_time DESC LIMIT 10",
    fetch=True
) or []

print(f"🔍 RECENT CHECKPOST SCANS (last 10)\n")
if scans:
    for s in scans:
        icon = "✅" if s["status"] == "PASS" else "❌"
        print(f"  {icon} {s['ticket_number']}  →  {s['checkpost_name']}")
        print(f"     Officer: {s['officer_name']}  |  Time: {s['scan_time']}")
        print()
else:
    print("  No scans recorded yet.")

print("=" * 55)
print("  Cross-check: every ticket_number in DB should")
print("  have a matching .png in qrcodes/ and .pdf in tickets/")
print("=" * 55)