# modules/qr_generator.py
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import qrcode
from config import QR_DIR


def generate_qr(ticket_number):
    """
    Creates a QR code PNG for the given ticket number.
    Returns the full path to the saved file.
    """
    # Make sure the folder exists
    os.makedirs(QR_DIR, exist_ok=True)

    # The data stored inside the QR code
    qr_data = ticket_number

    # Build the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save path
    filename  = f"{ticket_number}.png"
    save_path = os.path.join(QR_DIR, filename)

    print(f"[QR] Saving to : {save_path}")

    try:
        img.save(save_path)
        print(f"[QR] Save OK   : {os.path.exists(save_path)}")
        print(f"[QR] File size : {os.path.getsize(save_path)} bytes")
    except Exception as e:
        print(f"[QR] SAVE FAILED: {e}")
        return None

    return save_path


def get_qr_path(ticket_number):
    """
    Returns path to existing QR or generates a new one.
    """
    filename = f"{ticket_number}.png"
    path     = os.path.join(QR_DIR, filename)

    if not os.path.exists(path):
        return generate_qr(ticket_number)
    return path


# ── Self test ─────────────────────────────
if __name__ == "__main__":
    print("QR_DIR:", QR_DIR)
    path = generate_qr("NPL-2026-00001")
    if path:
        print(f"\nSuccess! Open this folder to see the QR:")
        print(f"  {QR_DIR}")