# modules/pdf_generator.py
# ============================================================
# Generates ONE A4 page with THREE permit copies:
#
#   TOP    (1/3 page)  — TRAVELLER COPY  — blue background
#   MIDDLE (1/3 page)  — ADMIN COPY 1    — white background
#   BOTTOM (1/3 page)  — ADMIN COPY 2    — light gray background
#
# Dashed cut lines separate each section.
#
# Drop-in replacement for the old 2-copy pdf_generator.py.
# All callers (ticket_printer.py etc.) use generate_ticket_pdf()
# — signature is unchanged.
# ============================================================

import os
import sys
import io
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader

from config import NEPAL_LOGO, TICKETS_DIR, ASSETS_DIR


# ── Colors ────────────────────────────────────────────────────
BLACK       = colors.black
WHITE       = colors.white
DARK_GRAY   = colors.HexColor("#333333")
LIGHT_GRAY  = colors.HexColor("#f5f5f5")
MID_GRAY    = colors.HexColor("#cccccc")
RED_NOTES   = colors.HexColor("#c0392b")
BLUE_DARK   = colors.HexColor("#003399")
BLUE_MED    = colors.HexColor("#1a4db3")
BLUE_LIGHT  = colors.HexColor("#dce8ff")
ADMIN_HDR   = colors.HexColor("#2c3e50")
ADMIN_BG    = colors.HexColor("#f8f9fa")
ADMIN_LINE  = colors.HexColor("#bdc3c7")
BORDER      = colors.HexColor("#999999")
DASHED      = colors.HexColor("#555555")
YELLOW_BADGE = colors.HexColor("#ffc200")


# ── Helpers ───────────────────────────────────────────────────

def _val(v, fallback=""):
    if v is None:
        return fallback
    s = str(v).strip()
    return s if s else fallback


def _format_date(val):
    """Return YYYY-MM-DD string from a date object or string."""
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    return s[:10] if len(s) >= 10 else s


def _gender_full(g):
    return {"M": "Male", "F": "Female", "O": "Other"}.get(g, g)


def _draw_logo(c, x, y, size):
    """Draw Nepal / NTNC logo if available, otherwise draw a placeholder circle."""
    logo_path = NEPAL_LOGO
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, x, y, width=size, height=size,
                        preserveAspectRatio=True, mask="auto")
            return
        except Exception as e:
            print(f"[PDF] Logo error: {e}")
    # Fallback circle placeholder
    c.setFillColor(colors.HexColor("#ccddff"))
    c.circle(x + size / 2, y + size / 2, size / 2, fill=1, stroke=0)
    c.setFillColor(BLUE_DARK)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x + size / 2, y + size / 2 - 3, "NTNC")


def _draw_photo(c, photo_path, x, y, w, h):
    """Draw tourist photo or placeholder."""
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
    c.setFont("Helvetica", 7)
    c.drawCentredString(x + w / 2, y + h / 2, "PHOTO")


def _make_qr_image_reader(data):
    """Generate QR code and return a ReportLab ImageReader."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _draw_qr(c, qr_path, ticket_number, x, y, size):
    """Draw QR from file path (existing behaviour) or generate on the fly."""
    if qr_path and os.path.exists(str(qr_path)):
        try:
            c.drawImage(qr_path, x, y, width=size, height=size,
                        preserveAspectRatio=True, mask="auto")
            return
        except Exception as e:
            print(f"[PDF] QR file error: {e}")
    # Generate in memory as fallback
    try:
        reader = _make_qr_image_reader(ticket_number)
        c.drawImage(reader, x, y, width=size, height=size,
                    preserveAspectRatio=True, mask="auto")
    except Exception as e:
        print(f"[PDF] QR generate error: {e}")
        c.setFillColor(LIGHT_GRAY)
        c.rect(x, y, size, size, fill=1, stroke=1)
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + size / 2, y + size / 2, "QR")


def _dashed_cut_line(c, x1, y, x2):
    """Draw a dashed horizontal cut line with a scissors symbol."""
    c.saveState()
    c.setStrokeColor(DASHED)
    c.setLineWidth(0.6)
    c.setDash([4, 3])
    c.line(x1 + 14, y, x2, y)
    c.restoreState()
    c.setFillColor(DASHED)
    c.setFont("Helvetica", 10)
    c.drawString(x1, y - 4, "\u2702")          # ✂
    c.setFont("Helvetica-Oblique", 6)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(x1 + 16, y + 1.5, "cut here")


def _badge(c, x, y, w, h, label, bg_color, text_color=WHITE, font_size=6.5):
    """Draw a rounded-rect badge with centred label."""
    c.setFillColor(bg_color)
    c.roundRect(x, y, w, h, 3, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", font_size)
    c.drawCentredString(x + w / 2, y + (h - font_size * 0.72) / 2, label)


# ══════════════════════════════════════════════════════════════
# COPY 1 — TRAVELLER COPY  (blue background)
# ══════════════════════════════════════════════════════════════

def _draw_traveller_copy(c, td, x, y, W, H):
    M = 0.5 * cm

    # ── Background ──
    c.setFillColor(BLUE_LIGHT)
    c.rect(x, y, W, H, fill=1, stroke=0)

    # ── Header bar ──
    hdr_h = 1.65 * cm
    hdr_y = y + H - hdr_h
    c.setFillColor(BLUE_DARK)
    c.rect(x, hdr_y, W, hdr_h, fill=1, stroke=0)

    # Logo in header
    logo_size = hdr_h * 0.82
    _draw_logo(c, x + M, hdr_y + (hdr_h - logo_size) / 2, logo_size)

    # Header text
    text_x = x + M + logo_size + 0.3 * cm
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(text_x, hdr_y + 1.12 * cm, "NATIONAL TRUST FOR NATURE CONSERVATION")
    c.setFont("Helvetica", 7.5)
    c.drawString(text_x, hdr_y + 0.72 * cm,
                 "Annapurna Conservation Area Project (ACAP)")
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(text_x, hdr_y + 0.35 * cm,
                 "Entry Permit / Entry Fee Receipt")

    # "TRAVELLER COPY" badge – top right
    bw, bh = 3.0 * cm, 0.52 * cm
    _badge(c, x + W - bw - M, hdr_y + (hdr_h - bh) / 2,
           bw, bh, "\u2708  TRAVELLER COPY", YELLOW_BADGE, BLACK, 6.5)

    # Header bottom rule
    c.setStrokeColor(BLUE_MED)
    c.setLineWidth(0.5)
    c.line(x, hdr_y, x + W, hdr_y)

    # ── Content zone ──
    content_top = hdr_y - 0.2 * cm
    note_h      = 0.9 * cm
    content_bot = y + note_h + 0.1 * cm

    # Photo
    photo_w, photo_h = 2.1 * cm, 2.5 * cm
    photo_x = x + M
    photo_y = content_top - photo_h - 0.1 * cm
    _draw_photo(c, td.get("photo_path"), photo_x, photo_y, photo_w, photo_h)

    # QR
    qr_size = 2.6 * cm
    qr_x = x + W - M - qr_size
    qr_y = content_top - qr_size - 0.05 * cm
    ticket_number = _val(td.get("ticket_number"))
    _draw_qr(c, td.get("_qr_path"), ticket_number, qr_x, qr_y, qr_size)

    # Ticket ref above QR
    permit_ref = _val(td.get("permit_ref"), ticket_number)
    c.setFillColor(BLUE_DARK)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(qr_x + qr_size / 2, qr_y + qr_size + 0.15 * cm, permit_ref)

    # Serial below QR
    serial = _val(td.get("serial_code"))
    if serial:
        c.setFont("Helvetica", 6)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 0.25 * cm, serial)

    # Fields
    field_x = photo_x + photo_w + 0.4 * cm
    lw      = 3.0 * cm
    nat     = _val(td.get("nationality"))
    gender  = _gender_full(_val(td.get("gender")))
    nat_display = f"{nat}  ({gender})" if gender else nat

    entry   = _format_date(td.get("entry_date"))
    expiry  = _format_date(td.get("expiry_date"))
    issue   = _format_date(td.get("created_at"))

    destination = _val(td.get("destination"), _val(td.get("sub_area")))
    permit_code = _val(td.get("permit_code"), ticket_number)
    permit_cost = _val(td.get("permit_cost"), "NPR. 1,000 (13% VAT incl.)")
    el_code     = _val(td.get("el_code"))

    fields = [
        ("Full Name",        _val(td.get("full_name"))),
        ("Passport No.",     _val(td.get("passport_number"))),
        ("Nationality",      nat_display),
        ("Destination",      destination),
        ("Entry Date",       entry),
        ("Expiry Date",      expiry),
        ("Permit Code",      permit_code),
        ("Date of Issue",    issue),
        ("Permit Cost",      permit_cost),
    ]

    fy      = content_top - 0.15 * cm
    line_h  = 0.46 * cm
    for label, value in fields:
        if fy - line_h < content_bot:
            break
        fy -= line_h
        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 7.5)
        lbl_str = f"{label} : "
        lbl_w   = c.stringWidth(lbl_str, "Helvetica", 7.5)
        c.drawString(field_x, fy, lbl_str)
        c.setFillColor(BLUE_DARK)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(field_x + lbl_w, fy, value)

    if el_code and fy - 0.38 * cm > content_bot:
        fy -= 0.38 * cm
        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 7)
        c.drawString(field_x, fy, el_code)

    # ── Important notes strip ──
    note_y = y + 0.05 * cm
    c.setFillColor(colors.HexColor("#fff3cd"))
    c.rect(x + M, note_y, W - 2 * M, note_h - 0.05 * cm, fill=1, stroke=0)
    c.setFillColor(RED_NOTES)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + M + 3 * mm, note_y + 0.57 * cm, "Important : ")
    c.setFont("Helvetica", 6.8)
    c.setFillColor(BLACK)
    c.drawString(x + M + 1.85 * cm, note_y + 0.57 * cm,
                 "Carry this permit + valid passport + visa. Non-transferable. Single entry only.")
    c.drawString(x + M + 3 * mm, note_y + 0.22 * cm,
                 "Valid only for designated area. Non-refundable. Present upon request at all checkposts.")

    # Agency line
    agency = _val(td.get("agency"))
    if agency:
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 7)
        aw = c.stringWidth("Agency : ", "Helvetica-Bold", 7)
        c.drawString(x + M, note_y - 0.3 * cm, "Agency : ")
        c.setFont("Helvetica", 7)
        c.drawString(x + M + aw, note_y - 0.3 * cm, agency)

    # ── Outer border ──
    c.setStrokeColor(BLUE_MED)
    c.setLineWidth(1.2)
    c.rect(x, y, W, H, fill=0, stroke=1)


# ══════════════════════════════════════════════════════════════
# COPY 2 & 3 — ADMIN COPIES  (white / light-gray)
# ══════════════════════════════════════════════════════════════

def _draw_admin_copy(c, td, x, y, W, H, copy_num=1):
    M = 0.5 * cm

    # ── Background ──
    bg = WHITE if copy_num == 1 else ADMIN_BG
    c.setFillColor(bg)
    c.rect(x, y, W, H, fill=1, stroke=0)

    # ── Header bar ──
    hdr_h = 1.25 * cm
    hdr_y = y + H - hdr_h
    c.setFillColor(ADMIN_HDR)
    c.rect(x, hdr_y, W, hdr_h, fill=1, stroke=0)

    # Logo
    logo_size = hdr_h * 0.82
    _draw_logo(c, x + M, hdr_y + (hdr_h - logo_size) / 2, logo_size)

    # Header text
    text_x = x + M + logo_size + 0.3 * cm
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(text_x, hdr_y + 0.75 * cm,
                 "NATIONAL TRUST FOR NATURE CONSERVATION  —  ACAP")
    c.setFont("Helvetica", 6.5)
    c.drawString(text_x, hdr_y + 0.35 * cm,
                 "Entry Permit / Fee Receipt  |  Administration Copy")

    # Badge
    badge_label  = f"ADMIN COPY {copy_num}"
    badge_color  = colors.HexColor("#e74c3c") if copy_num == 1 else colors.HexColor("#27ae60")
    bw, bh = 2.6 * cm, 0.48 * cm
    _badge(c, x + W - bw - M, hdr_y + (hdr_h - bh) / 2,
           bw, bh, badge_label, badge_color, WHITE, 6.5)

    # ── Content zone ──
    content_top = hdr_y - 0.15 * cm
    sig_h       = 0.75 * cm        # signature strip height at bottom
    content_bot = y + sig_h + 0.1 * cm

    # QR
    qr_size = 2.0 * cm
    qr_x    = x + W - M - qr_size
    qr_y    = content_top - qr_size - 0.05 * cm
    ticket_number = _val(td.get("ticket_number"))
    _draw_qr(c, td.get("_qr_path"), ticket_number, qr_x, qr_y, qr_size)

    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 0.2 * cm, ticket_number)

    # ── Two-column fields ──
    nat    = _val(td.get("nationality"))
    gender = _gender_full(_val(td.get("gender")))
    nat_display = f"{nat} ({gender})" if gender else nat

    entry  = _format_date(td.get("entry_date"))
    expiry = _format_date(td.get("expiry_date"))
    issue  = _format_date(td.get("created_at"))

    destination = _val(td.get("destination"), _val(td.get("sub_area")))
    permit_code = _val(td.get("permit_code"), ticket_number)
    permit_cost = _val(td.get("permit_cost"), "NPR. 1,000 (13% VAT incl.)")
    created_by  = _val(td.get("created_by"))

    col1_fields = [
        ("Full Name",    _val(td.get("full_name"))),
        ("Passport No.", _val(td.get("passport_number"))),
        ("Nationality",  nat_display),
        ("Permit Code",  permit_code),
    ]
    col2_fields = [
        ("Destination",  destination),
        ("Entry Date",   entry),
        ("Expiry Date",  expiry),
        ("Permit Cost",  permit_cost),
    ]

    col1_x  = x + M
    col2_x  = x + W * 0.46
    lw      = 2.6 * cm
    fy      = content_top - 0.15 * cm
    line_h  = 0.41 * cm

    for (l1, v1), (l2, v2) in zip(col1_fields, col2_fields):
        # Col 1
        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 7)
        lw1 = c.stringWidth(f"{l1} : ", "Helvetica", 7)
        c.drawString(col1_x, fy, f"{l1} : ")
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(col1_x + lw1, fy, v1)
        # Col 2
        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 7)
        lw2 = c.stringWidth(f"{l2} : ", "Helvetica", 7)
        c.drawString(col2_x, fy, f"{l2} : ")
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(col2_x + lw2, fy, v2)
        # Separator line
        c.setStrokeColor(ADMIN_LINE)
        c.setLineWidth(0.3)
        c.line(col1_x, fy - 0.06 * cm, qr_x - 0.3 * cm, fy - 0.06 * cm)
        fy -= line_h

    # ── Bottom strip: permit code + issued by ──
    strip_h = 0.48 * cm
    strip_y = y + sig_h + 0.05 * cm
    c.setFillColor(LIGHT_GRAY)
    c.rect(x + M, strip_y, W - 2 * M, strip_h, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + M + 3 * mm, strip_y + 0.15 * cm,
                 f"Permit Code: {permit_code}   |   Fee Paid: {permit_cost}"
                 + (f"   |   Issued by: {created_by}" if created_by else ""))

    # ── Signature line ──
    sig_line_x = x + W - 5 * cm
    sig_line_y = y + 0.38 * cm
    c.setStrokeColor(DARK_GRAY)
    c.setLineWidth(0.5)
    c.line(sig_line_x, sig_line_y, sig_line_x + 4.3 * cm, sig_line_y)
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(sig_line_x + 2.15 * cm, y + 0.1 * cm,
                        "Authorized Signature / Stamp")

    # Date of print (admin accountability)
    from datetime import date as _date
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(x + M, y + 0.1 * cm, f"Printed: {_date.today()}")

    # ── Outer border ──
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.rect(x, y, W, H, fill=0, stroke=1)


# ══════════════════════════════════════════════════════════════
# PUBLIC API  — same signature as the old generate_ticket_pdf()
# ══════════════════════════════════════════════════════════════

def generate_ticket_pdf(tourist_data, scan_history=None):
    """
    Generates one A4 PDF with THREE permit copies (top=traveller blue,
    middle=admin 1, bottom=admin 2) separated by dashed cut lines.

    tourist_data keys  (same as before):
        ticket_number, full_name, passport_number, nationality, gender,
        photo_path, destination, sub_area, entry_date, expiry_date,
        permit_code, permit_cost, el_code, serial_code, permit_ref,
        agency, created_by, created_at

    Returns the path to the saved PDF file.
    """
    if scan_history is None:
        scan_history = []

    ticket_number = tourist_data["ticket_number"]

    # Attach QR path (same logic as before — uses your qr_generator module)
    from modules.qr_generator import get_qr_path
    tourist_data["_qr_path"] = get_qr_path(ticket_number)

    pdf_path = os.path.join(TICKETS_DIR, f"{ticket_number}.pdf")
    os.makedirs(TICKETS_DIR, exist_ok=True)

    W, H   = A4              # 595 x 842 pt
    P_M    = 0.45 * cm       # page margin
    inner_w = W - 2 * P_M
    sec_h  = (H - 2 * P_M) / 3   # each of the three equal sections

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Entry Permit — {ticket_number}")

    # y-coordinates (bottom-up, so index 0 = bottom)
    y0 = P_M                   # bottom section  → Admin Copy 2
    y1 = P_M + sec_h           # middle section  → Admin Copy 1
    y2 = P_M + 2 * sec_h       # top section     → Traveller Copy

    _draw_traveller_copy(c, tourist_data, P_M, y2, inner_w, sec_h)
    _draw_admin_copy    (c, tourist_data, P_M, y1, inner_w, sec_h, copy_num=1)
    _draw_admin_copy    (c, tourist_data, P_M, y0, inner_w, sec_h, copy_num=2)

    # Dashed cut lines between sections
    _dashed_cut_line(c, P_M, y2, W - P_M)          # between traveller & admin-1
    _dashed_cut_line(c, P_M, y1, W - P_M)          # between admin-1 & admin-2

    c.save()
    print(f"[PDF] 3-copy permit saved: {pdf_path}")
    return pdf_path


# ══════════════════════════════════════════════════════════════
# SELF-TEST  (run: python modules/pdf_generator.py)
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    fake = {
        "ticket_number":   "NPL-2026-00001",
        "full_name":       "PATEL NAVYABEN RAJESH",
        "passport_number": "820802919243",
        "nationality":     "India",
        "gender":          "F",
        "photo_path":      None,
        "destination":     "Jomsom Muktinath Trek",
        "sub_area":        "",
        "entry_date":      "2026-05-25",
        "expiry_date":     "2026-06-02",
        "permit_code":     "ONTP4dsy1 / 260525TydN1XW3",
        "permit_cost":     "NPR. 1,000 (13% VAT included)",
        "el_code":         "EL43iaJoy1",
        "serial_code":     "653274068-C-Y8",
        "permit_ref":      "ONL/ACAP-250432",
        "agency":          "Balaji Diyo Tours and Trekking, Lakeside  |  Tel: 9856044470",
        "created_by":      "Officer Test",
        "created_at":      "2026-05-25",
    }

    path = generate_ticket_pdf(fake, [])
    print(f"\nPDF saved: {path}")
    import subprocess
    try:
        subprocess.Popen(["start", path], shell=True)
    except Exception:
        pass