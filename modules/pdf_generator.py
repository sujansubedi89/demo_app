# modules/pdf_generator.py
# ============================================
# Generates the printable PDF ticket
# ============================================

import os
import sys
from datetime import datetime
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
# ReportLab is the PDF library
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


from config import NEPAL_LOGO, TICKETS_DIR, CHECKPOSTS, ASSETS_DIR


# ── Colors ────────────────────────────────
RED         = colors.HexColor("#C0392B")   # Nepal flag red
DARK_RED    = colors.HexColor("#922B21")
BLUE        = colors.HexColor("#1A5276")   # deep blue for text
LIGHT_GRAY  = colors.HexColor("#F2F3F4")
MID_GRAY    = colors.HexColor("#BDC3C7")
DARK_GRAY   = colors.HexColor("#2C3E50")
WHITE       = colors.white
BLACK       = colors.black
GREEN       = colors.HexColor("#1E8449")
GOLD        = colors.HexColor("#B7950B")


def draw_header(c, width, height):
    """
    Draws the top section:
    Nepal logo | GOVERNMENT OF NEPAL | TOURIST ENTRY PERMIT
    """
    # Red background bar across the top
    c.setFillColor(RED)
    c.rect(0, height - 3.5*cm, width, 3.5*cm, fill=1, stroke=0)

    # Dark red bottom strip on header
    c.setFillColor(DARK_RED)
    c.rect(0, height - 3.7*cm, width, 0.2*cm, fill=1, stroke=0)

    # Nepal logo (top left of header)
    logo_x = 0.8*cm
    logo_y = height - 3.2*cm
    logo_size = 2.5*cm

    if os.path.exists(NEPAL_LOGO):
        try:
            c.drawImage(
                NEPAL_LOGO,
                logo_x, logo_y,
                width=logo_size, height=logo_size,
                preserveAspectRatio=True,
                mask="auto"
            )
        except Exception as e:
            print(f"[PDF] Could not load logo: {e}")

    # "GOVERNMENT OF NEPAL" text
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(4.2*cm, height - 1.6*cm, "GOVERNMENT OF NEPAL")

    # "Department of Immigration" subtitle
    c.setFont("Helvetica", 10)
    c.drawString(4.2*cm, height - 2.2*cm, "Department of Immigration")

    # "TOURIST ENTRY PERMIT" big text (right side)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(width - 0.8*cm, height - 1.6*cm, "TOURIST ENTRY PERMIT")

    c.setFont("Helvetica", 9)
    c.drawRightString(width - 0.8*cm, height - 2.2*cm, "पर्यटक प्रवेश अनुमतिपत्र")  # Nepali


def draw_ticket_number_bar(c, width, height, ticket_number):
    """
    Draws the ticket number bar just below the header.
    """
    bar_y = height - 4.4*cm
    c.setFillColor(DARK_GRAY)
    c.rect(0, bar_y, width, 0.7*cm, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(0.8*cm, bar_y + 0.15*cm, f"Ticket No:  {ticket_number}")

    # Print date on the right
    now = datetime.now().strftime("%d %b %Y  %H:%M")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 0.8*cm, bar_y + 0.15*cm, f"Printed: {now}")


def draw_photo(c, photo_path, x, y, box_w, box_h):
    """
    Draws the tourist photo inside a bordered box.
    If no photo, draws a placeholder box.
    """
    # Border around photo
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(1)
    c.rect(x, y, box_w, box_h, fill=0, stroke=1)

    placeholder_path = os.path.join(ASSETS_DIR, "placeholder_photo.png")

    if photo_path and os.path.exists(str(photo_path)):
        use_path = photo_path
    elif os.path.exists(placeholder_path):
        use_path = placeholder_path
    else:
        use_path = None

    if use_path:
        try:
            c.drawImage(
                use_path,
                x + 1*mm, y + 1*mm,
                width  = box_w - 2*mm,
                height = box_h - 2*mm,
                preserveAspectRatio=True,
                mask="auto"
            )
        except Exception as e:
            print(f"[PDF] Photo load failed: {e}")
            _draw_photo_placeholder(c, x, y, box_w, box_h)
    else:
        _draw_photo_placeholder(c, x, y, box_w, box_h)


def _draw_photo_placeholder(c, x, y, box_w, box_h):
    """Draws a gray box with 'PHOTO' text when no photo is available."""
    c.setFillColor(LIGHT_GRAY)
    c.rect(x + 1*mm, y + 1*mm, box_w - 2*mm, box_h - 2*mm, fill=1, stroke=0)
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 10)
    c.drawCentredString(x + box_w/2, y + box_h/2, "PHOTO")


def draw_field(c, label, value, x, y, label_width=3.5*cm, value_width=7*cm):
    """
    Draws one label-value pair.
    label: "Full Name"
    value: "John Michael Doe"
    """
    # Label (bold, dark blue)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, label + ":")

    # Value (black, regular)
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 10)
    c.drawString(x + label_width, y, str(value) if value else "—")

    # Underline below the whole field
    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(x, y - 2*mm, x + label_width + value_width, y - 2*mm)


def draw_checkposts_section(c, x, y, width, scan_history):
    """
    Draws the checkpost status grid.
    Shows each checkpost with a checkbox — ticked if tourist passed through it.
    scan_history = list of dicts from get_tourist_checkpost_history()
    """
    # Section header
    c.setFillColor(BLUE)
    c.rect(x, y, width, 0.6*cm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 0.3*cm, y + 0.15*cm, "CHECKPOST RECORD")

    y_cursor = y - 0.5*cm

    # Build a set of checkposts this tourist has passed
    passed = set()
    pass_times = {}
    for log in scan_history:
        if log["status"] == "PASS":
            passed.add(log["checkpost_name"])
            pass_times[log["checkpost_name"]] = log["scan_time"]

    col_width = width / 2
    checkpost_list = CHECKPOSTS

    for i, cp_name in enumerate(checkpost_list):
        col = i % 2           # 0 = left column, 1 = right column
        row = i // 2

        cx = x + col * col_width + 0.3*cm
        cy = y_cursor - row * 1.0*cm

        has_passed = cp_name in passed

        # Checkbox square
        c.setStrokeColor(DARK_GRAY)
        c.setLineWidth(0.8)
        c.rect(cx, cy, 0.4*cm, 0.4*cm, fill=0, stroke=1)

        if has_passed:
            # Green tick inside box
            c.setStrokeColor(GREEN)
            c.setLineWidth(1.5)
            c.line(cx + 0.05*cm, cy + 0.2*cm,  cx + 0.15*cm, cy + 0.08*cm)
            c.line(cx + 0.15*cm, cy + 0.08*cm, cx + 0.38*cm, cy + 0.35*cm)

        # Checkpost name
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold" if has_passed else "Helvetica", 9)
        c.drawString(cx + 0.55*cm, cy + 0.1*cm, cp_name)

        # Scan time (if passed)
        if has_passed and cp_name in pass_times:
            scan_dt = pass_times[cp_name]
            if isinstance(scan_dt, datetime):
                time_str = scan_dt.strftime("%d %b %Y %H:%M")
            else:
                time_str = str(scan_dt)
            c.setFont("Helvetica", 7)
            c.setFillColor(GREEN)
            c.drawString(cx + 0.55*cm, cy - 0.15*cm, time_str)
            c.setFillColor(BLACK)

    return y_cursor - ((len(checkpost_list) // 2 + 1) * 1.0*cm)


def draw_qr_code(c, qr_path, x, y, size):
    """
    Draws the QR code image on the ticket.
    """
    if qr_path and os.path.exists(qr_path):
        c.drawImage(
            qr_path,
            x, y,
            width=size, height=size,
            preserveAspectRatio=True,
            mask="auto"
        )
    else:
        # Placeholder if QR not found
        c.setFillColor(LIGHT_GRAY)
        c.rect(x, y, size, size, fill=1, stroke=1)
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + size/2, y + size/2, "QR CODE")


def draw_footer(c, width):
    """
    Draws the bottom strip with legal notice and validity reminder.
    """
    footer_height = 1.5*cm

    c.setFillColor(DARK_GRAY)
    c.rect(0, 0, width, footer_height, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(0.8*cm, 0.95*cm, "IMPORTANT:")

    c.setFont("Helvetica", 7.5)
    c.drawString(0.8*cm, 0.6*cm,
        "This permit must be presented at all checkposts. "
        "Failure to produce this document may result in penalties.")

    c.drawString(0.8*cm, 0.25*cm,
        "This is an official Government of Nepal document. Tampering is a criminal offence.")


def generate_ticket_pdf(tourist_data, scan_history=None):
    """
    MAIN FUNCTION — call this to generate the full PDF ticket.

    tourist_data = dict from get_tourist_by_ticket()
    scan_history = list from get_tourist_checkpost_history() (optional)

    Returns the path to the saved PDF.
    """
    if scan_history is None:
        scan_history = []

    ticket_number = tourist_data["ticket_number"]

    # ── Generate QR code first ────────────
    from modules.qr_generator import get_qr_path
    qr_path = get_qr_path(ticket_number)

    # ── PDF file path ─────────────────────
    pdf_path = os.path.join(TICKETS_DIR, f"{ticket_number}.pdf")

    # ── Page setup ────────────────────────
    page_width, page_height = A4          # 595 x 842 points
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Nepal Tourist Entry Permit — {ticket_number}")

    # ── Draw all sections ─────────────────

    # 1. Header (Nepal logo + title)
    draw_header(c, page_width, page_height)

    # 2. Ticket number bar
    draw_ticket_number_bar(c, page_width, page_height, ticket_number)

    # ── Main content area ─────────────────
    content_y = page_height - 5.5*cm    # start drawing below header+bar
    margin_l  = 0.8*cm
    photo_w   = 3.5*cm
    photo_h   = 4.5*cm

    # 3. Tourist photo (left side)
    draw_photo(
        c,
        tourist_data.get("photo_path"),
        x = margin_l,
        y = content_y - photo_h,
        box_w = photo_w,
        box_h = photo_h,
    )

    # 4. Personal details (right of photo)
    field_x = margin_l + photo_w + 0.5*cm
    field_y = content_y - 0.6*cm
    line_h  = 0.85*cm

    fields = [
        ("Full Name",      tourist_data.get("full_name", "")),
        ("Passport No",    tourist_data.get("passport_number", "")),
        ("Nationality",    tourist_data.get("nationality", "")),
        ("Visa Type",      tourist_data.get("visa_type", "")),
        ("Vehicle Type",   tourist_data.get("vehicle_type", "None")),
        ("Vehicle No",     tourist_data.get("vehicle_number", "") or "—"),
    ]

    for label, value in fields:
        draw_field(c, label, value, field_x, field_y)
        field_y -= line_h

    # 5. Dates section (below photo)
    date_y = content_y - photo_h - 0.8*cm

    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_l, date_y, "Entry Date:")
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 10)

    entry = tourist_data.get("entry_date", "")
    expiry = tourist_data.get("expiry_date", "")

    if hasattr(entry, "strftime"):
        entry = entry.strftime("%d %B %Y")
    if hasattr(expiry, "strftime"):
        expiry = expiry.strftime("%d %B %Y")

    c.drawString(margin_l + 2.8*cm, date_y, str(entry))

    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_l + 8*cm, date_y, "Valid Until:")
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_l + 10.8*cm, date_y, str(expiry))

    # Divider line
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(0.5)
    c.line(margin_l, date_y - 0.4*cm, page_width - margin_l, date_y - 0.4*cm)

    # 6. Checkpost section
    cp_y = date_y - 1.0*cm
    cp_width = page_width - margin_l - 4.5*cm    # leave room for QR on right

    draw_checkposts_section(
        c,
        x     = margin_l,
        y     = cp_y,
        width = cp_width,
        scan_history = scan_history,
    )

    # 7. QR code (bottom right of content area)
    qr_size = 3.8*cm
    qr_x = page_width - qr_size - 0.8*cm
    qr_y = cp_y - qr_size - 0.3*cm + 0.6*cm

    draw_qr_code(c, qr_path, qr_x, qr_y, qr_size)

    # QR label below it
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 7)
    c.drawCentredString(qr_x + qr_size/2, qr_y - 0.35*cm, "Scan at each checkpost")

    # 8. Created by info
    officer_y = 2.5*cm
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(margin_l, officer_y,
        f"Issued by: {tourist_data.get('created_by', '')}   |   "
        f"Issued at: {tourist_data.get('created_at', '')}")

    # 9. Footer
    draw_footer(c, page_width)

    # ── Save the PDF ──────────────────────
    c.save()
    print(f"[PDF] Ticket generated: {pdf_path}")
    return pdf_path


# ── Self test ─────────────────────────────
if __name__ == "__main__":
    # Fake tourist data to test PDF generation without a real DB entry
    fake_tourist = {
        "ticket_number":   "NPL-2026-00001",
        "full_name":       "John Michael Doe",
        "passport_number": "A12345678",
        "nationality":     "United States of America",
        "photo_path":      None,
        "visa_type":       "Tourist",
        "vehicle_type":    "Car",
        "vehicle_number":  "BA 1 KHA 2345",
        "entry_date":      "15 May 2026",
        "expiry_date":     "14 June 2026",
        "created_by":      "Officer Ram Sharma",
        "created_at":      "2026-05-15 10:30:00",
    }

    fake_scans = [
        {
            "checkpost_name": "Birgunj",
            "officer_name":   "Ram Sharma",
            "scan_time":      datetime.now(),
            "status":         "PASS",
        }
    ]

    pdf_path = generate_ticket_pdf(fake_tourist, fake_scans)
    print(f"\nPDF created at: {pdf_path}")
    print("Open the tickets/ folder to see it!")

    # Auto-open the PDF on Windows
    import subprocess
    try:
        subprocess.Popen(["start", pdf_path], shell=True)
    except:
        pass