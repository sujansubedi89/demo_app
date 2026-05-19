# modules/pdf_generator.py
# ============================================
# Generates permit exactly matching ACAP style
# - Top half  : Entry Permit / Entry Fee Receipt
# - Bottom half: Check Post Copy
# Both on ONE A4 page
# ============================================

import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm

from config import NEPAL_LOGO, TICKETS_DIR, ASSETS_DIR


# ── Colors ────────────────────────────────
BLACK      = colors.black
WHITE      = colors.white
DARK_GRAY  = colors.HexColor("#333333")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MID_GRAY   = colors.HexColor("#cccccc")
RED_NOTES  = colors.HexColor("#c0392b")
BLUE_HDR   = colors.HexColor("#003399")
BORDER     = colors.HexColor("#999999")


def _val(v, fallback=""):
    if v is None:
        return fallback
    s = str(v).strip()
    return s if s else fallback


def _draw_photo(c, photo_path, x, y, w, h):
    placeholder = os.path.join(ASSETS_DIR, "placeholder_photo.png")
    use = None
    if photo_path and os.path.exists(str(photo_path)):
        use = photo_path
    elif os.path.exists(placeholder):
        use = placeholder

    if use:
        try:
            c.drawImage(use, x, y, width=w, height=h,
                        preserveAspectRatio=True, mask="auto")
            return
        except Exception as e:
            print(f"[PDF] Photo error: {e}")

    c.setFillColor(LIGHT_GRAY)
    c.rect(x, y, w, h, fill=1, stroke=1)
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + w/2, y + h/2, "PHOTO")


def _draw_qr(c, qr_path, x, y, size):
    if qr_path and os.path.exists(str(qr_path)):
        try:
            c.drawImage(qr_path, x, y, width=size, height=size,
                        preserveAspectRatio=True, mask="auto")
            return
        except Exception as e:
            print(f"[PDF] QR error: {e}")
    c.setFillColor(LIGHT_GRAY)
    c.rect(x, y, size, size, fill=1, stroke=1)
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 7)
    c.drawCentredString(x + size/2, y + size/2, "QR")


def _draw_permit_block(c, td, x, y, block_w, block_h, is_checkpost=False):
    """
    Draws one permit block (main permit OR checkpost copy).
    x, y        = bottom-left corner of the block
    block_w/h   = dimensions
    is_checkpost= True for the lower "Check Post Copy" section
    """
    W = block_w
    H = block_h
    M = 0.5 * cm
    top = y + H

    # Outer border
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.rect(x, y, W, H, fill=0, stroke=1)

    # ══════════════════════════
    # HEADER
    # ══════════════════════════
    if is_checkpost:
        hdr_h = 1.55 * cm
    else:
        hdr_h = 2.9 * cm

    hdr_bot = top - hdr_h

    # White background for header
    c.setFillColor(WHITE)
    c.rect(x, hdr_bot, W, hdr_h, fill=1, stroke=0)

    # Logo
    logo_size = hdr_h * 0.85
    logo_x = x + M
    logo_y = hdr_bot + (hdr_h - logo_size) / 2
    logo_path = NEPAL_LOGO
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, logo_x, logo_y,
                        width=logo_size, height=logo_size,
                        preserveAspectRatio=True, mask="auto")
        except Exception as e:
            print(f"[PDF] Logo error: {e}")

    if is_checkpost:
        # "Check Post Copy" italic centered
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(x + W / 2, hdr_bot + 1.1 * cm, "Check Post Copy")
        c.setFont("Helvetica-Bold", 12.5)
        c.drawCentredString(x + W / 2, hdr_bot + 0.62 * cm, "NATIONAL TRUST FOR NATURE CONSERVATION")
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + W / 2, hdr_bot + 0.2 * cm, "Annapurna Conservation Area Project (ACAP)")
    else:
        # Full header text to the right of the logo
        text_x = logo_x + logo_size + 0.3 * cm
        c.setFillColor(BLUE_HDR)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(text_x, hdr_bot + 2.2 * cm, "NATIONAL TRUST FOR NATURE CONSERVATION")

        c.setFillColor(BLACK)
        c.setFont("Helvetica", 10)
        c.drawString(text_x, hdr_bot + 1.65 * cm, "Entry Permit / Entry Fee Receipt")

        c.setFont("Helvetica", 6.8)
        c.drawString(text_x, hdr_bot + 1.2 * cm,
                     "Schedule -2 (Relating to Rule 19, Sub-Rule[1] of Conservation Area Management Rules 2053)")

        c.setFillColor(BLUE_HDR)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(text_x, hdr_bot + 0.6 * cm,
                     "Annapurna Conservation Area Project (ACAP)")

    # Header bottom rule
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(x, hdr_bot, x + W, hdr_bot)

    # ══════════════════════════
    # ACAP WATERMARK (main only)
    # ══════════════════════════
    if not is_checkpost:
        c.saveState()
        c.setFillColor(colors.HexColor("#d8ead8"))
        c.setFont("Helvetica-Bold", 80)
        # ReportLab doesn't expose setFillAlpha via canvas directly;
        # use transparency via color with alpha component workaround:
        # draw very lightly by using a near-white color instead
        content_mid_y = y + (H - hdr_h) / 2 + 0.5 * cm
        c.translate(x + W / 2, content_mid_y)
        c.rotate(8)
        c.drawCentredString(0, 0, "ACAP")
        c.restoreState()

    # ══════════════════════════
    # CONTENT AREA
    # ══════════════════════════
    content_top = hdr_bot - 0.2 * cm
    if is_checkpost:
        content_bot = y + 0.45 * cm
    else:
        content_bot = y + 2.55 * cm   # space for notes section

    # Photo (left)
    photo_w = 2.8 * cm if is_checkpost else 3.2 * cm
    photo_h = 3.1 * cm if is_checkpost else 3.6 * cm
    photo_x = x + M
    photo_y = content_top - photo_h - 0.1 * cm
    _draw_photo(c, td.get("photo_path"), photo_x, photo_y, photo_w, photo_h)

    # QR (right)
    qr_size = 2.7 * cm if is_checkpost else 3.2 * cm
    qr_x = x + W - M - qr_size
    qr_y = content_top - qr_size - 0.1 * cm
    _draw_qr(c, td.get("_qr_path"), qr_x, qr_y, qr_size)

    # Permit ref above QR
    permit_ref = _val(td.get("permit_ref"), _val(td.get("ticket_number")))
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(qr_x + qr_size / 2, qr_y + qr_size + 0.18 * cm, permit_ref)

    # Serial code below QR
    serial = _val(td.get("serial_code"), "")
    if serial:
        c.setFont("Helvetica", 7)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 0.3 * cm, serial)

    # Fields (center between photo and QR)
    field_x = photo_x + photo_w + 0.4 * cm
    field_right = qr_x - 0.2 * cm

    if is_checkpost:
        fs_lbl = 8
        fs_val = 9
        line_h = 0.5 * cm
    else:
        fs_lbl = 8.5
        fs_val = 10
        line_h = 0.58 * cm

    # Build nationality display (with gender initial: "India, F")
    nat = _val(td.get("nationality"))
    gender = _val(td.get("gender"), "")
    nat_display = f"{nat}, {gender[0].upper()}" if gender else nat

    # Dates
    entry  = _val(td.get("entry_date"),  "")
    expiry = _val(td.get("expiry_date"), "")
    if hasattr(td.get("entry_date"),  "strftime"):
        entry  = td["entry_date"].strftime("%Y-%m-%d")
    if hasattr(td.get("expiry_date"), "strftime"):
        expiry = td["expiry_date"].strftime("%Y-%m-%d")

    issue_date = _val(td.get("created_at"), "")
    if hasattr(td.get("created_at"), "strftime"):
        issue_date = td["created_at"].strftime("%Y-%m-%d")
    elif len(issue_date) > 10:
        issue_date = issue_date[:10]

    permit_code = _val(td.get("permit_code"), _val(td.get("ticket_number")))
    permit_cost = _val(td.get("permit_cost"), "NPR. 1000 (13% VAT included)")
    el_code     = _val(td.get("el_code"), "")
    destination = _val(td.get("destination"), _val(td.get("sub_area")))

    fields = [
        ("Full Name",       _val(td.get("full_name"))),
        ("Passport No.",    _val(td.get("passport_number"))),
        ("Nationality.",    nat_display),
        ("Destination",     destination),
        ("Entry-Exit Date", f"{entry} - {expiry}"),
        ("Permit Code",     permit_code),
        ("Date of Issue",   issue_date),
        ("Permit Cost",     permit_cost),
    ]

    fy = content_top - 0.1 * cm
    for label, value in fields:
        if fy - line_h < content_bot:
            break
        fy -= line_h

        c.setFillColor(BLACK)
        c.setFont("Helvetica", fs_lbl)
        label_str = f"{label} : "
        lw = c.stringWidth(label_str, "Helvetica", fs_lbl)
        c.drawString(field_x, fy, label_str)

        c.setFont("Helvetica-Bold", fs_val)
        c.drawString(field_x + lw, fy, value)

    # el_code on its own line
    if el_code and fy - 0.4 * cm > content_bot:
        fy -= 0.4 * cm
        c.setFont("Helvetica", fs_lbl)
        c.drawString(field_x, fy, el_code)

    # ══════════════════════════
    # IMPORTANT NOTES (main only)
    # ══════════════════════════
    if not is_checkpost:
        notes_top = y + 2.45 * cm
        notes_bot = y + 0.5 * cm
        note_bg   = colors.HexColor("#fffbf5")

        c.setFillColor(note_bg)
        c.rect(x + M, notes_bot, W - 2 * M, notes_top - notes_bot, fill=1, stroke=0)

        c.setFillColor(RED_NOTES)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x + M + 2 * mm, notes_top - 0.32 * cm, "Important Notes :")

        note_lines = [
            "- Permits are non-transferable and non-refundable—plan your trip carefully.",
            "- Valid for a single entry to the designated areas only and cannot be reused after exit.",
            "- Carry your permit (printed), valid passport, and visa—show upon request.",
        ]
        ny = notes_top - 0.65 * cm
        for line in note_lines:
            c.setFillColor(RED_NOTES)
            c.setFont("Helvetica", 7.5)
            c.drawString(x + M + 3 * mm, ny, line)
            ny -= 0.36 * cm

    # ══════════════════════════
    # AGENCY LINE
    # ══════════════════════════
    agency = _val(td.get("agency"), "")
    if agency:
        agency_y = y + 0.12 * cm
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 8)
        aw = c.stringWidth("Agency : ", "Helvetica-Bold", 8)
        c.drawString(x + M, agency_y, "Agency : ")
        c.setFont("Helvetica", 8)
        c.drawString(x + M + aw, agency_y, agency)


# ══════════════════════════════════════════
# MAIN PUBLIC FUNCTION
# ══════════════════════════════════════════

def generate_ticket_pdf(tourist_data, scan_history=None):
    """
    Generates one A4 page with:
      TOP    → Entry Permit / Entry Fee Receipt
      BOTTOM → Check Post Copy

    tourist_data keys:
        ticket_number, full_name, passport_number, nationality, gender,
        photo_path, destination, sub_area, entry_date, expiry_date,
        permit_code, permit_cost, el_code, serial_code, permit_ref,
        agency, created_by, created_at

    Returns path to the saved PDF.
    """
    if scan_history is None:
        scan_history = []

    ticket_number = tourist_data["ticket_number"]

    # Get/generate QR and attach to data dict for use inside blocks
    from modules.qr_generator import get_qr_path
    tourist_data["_qr_path"] = get_qr_path(ticket_number)

    pdf_path = os.path.join(TICKETS_DIR, f"{ticket_number}.pdf")
    W, H = A4   # 595 x 842 pt
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Entry Permit — {ticket_number}")

    page_margin = 0.6 * cm
    inner_w     = W - 2 * page_margin
    mid_y       = H / 2

    # Horizontal separator line between the two halves
    c.setStrokeColor(DARK_GRAY)
    c.setLineWidth(1.5)
    c.line(page_margin, mid_y, W - page_margin, mid_y)

    gap = 0.25 * cm   # gap between separator and each block

    # Top block: main permit
    main_y = mid_y + gap
    main_h = H - page_margin - main_y

    # Bottom block: checkpost copy
    cp_y = page_margin
    cp_h = mid_y - gap - page_margin

    _draw_permit_block(c, tourist_data,
                       x=page_margin, y=main_y,
                       block_w=inner_w, block_h=main_h,
                       is_checkpost=False)

    _draw_permit_block(c, tourist_data,
                       x=page_margin, y=cp_y,
                       block_w=inner_w, block_h=cp_h,
                       is_checkpost=True)

    c.save()
    print(f"[PDF] Permit saved: {pdf_path}")
    return pdf_path


# ══════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════
if __name__ == "__main__":
    fake = {
        "ticket_number":   "NPL-2026-00001",
        "full_name":       "PATEL NAVYABEN",
        "passport_number": "820802919243",
        "nationality":     "India",
        "gender":          "Female",
        "photo_path":      None,
        "destination":     "Jomsom Muktinath Trek",
        "sub_area":        "",
        "entry_date":      "2026-05-18",
        "expiry_date":     "2026-05-26",
        "permit_code":     "ONTP4dsy1 / 260518TydN1XW3",
        "permit_cost":     "NPR. 1000 (13% VAT included)",
        "el_code":         "EL43iaJoy1",
        "serial_code":     "653274068-C-Y8",
        "permit_ref":      "ONL/ACAP-250432",
        "agency":          "Balaji Diyo Tours and Trekking, ward no 6 Lakeside, Tel : 9856044470",
        "created_by":      "Officer Test",
        "created_at":      "2026-05-18",
        "visa_type":       "Tourism",
    }

    path = generate_ticket_pdf(fake, [])
    print(f"\nPDF saved: {path}")
    import subprocess
    try:
        subprocess.Popen(["start", path], shell=True)
    except:
        pass
