# # modules/ticket_creator.py
# import sys
# import os
# from datetime import date, timedelta

# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.insert(0, PROJECT_ROOT)

# from config import TICKET_PREFIX, TICKET_VALIDITY_DAYS
# from database.local_db import run_query


# def generate_ticket_number():
#     """
#     Generates next ticket number e.g. NPL-2026-00001
#     """
#     year = date.today().year

#     rows = run_query(
#         "SELECT ticket_number FROM tourists WHERE ticket_number LIKE %s ORDER BY id DESC LIMIT 1",
#         (f"{TICKET_PREFIX}-{year}-%",),
#         fetch=True
#     )

#     if rows:
#         last_ticket = rows[0]["ticket_number"]
#         last_number = int(last_ticket.split("-")[-1])
#         next_number = last_number + 1
#     else:
#         next_number = 1

#     return f"{TICKET_PREFIX}-{year}-{next_number:05d}"


# def save_tourist(data):
#     """
#     Saves tourist to DB. Returns ticket_number on success, None on failure.
#     """
#     # Generate ticket number FIRST before using it
#     ticket_number = generate_ticket_number()

#     sql = """
#         INSERT INTO tourists (
#             ticket_number, full_name, passport_number,
#             nationality, photo_path, visa_type,
#             vehicle_type, vehicle_number,
#             entry_date, expiry_date, created_by
#         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """

#     params = (
#         ticket_number,
#         data["full_name"],
#         data["passport_number"],
#         data["nationality"],
#         data.get("photo_path", None),
#         data["visa_type"],
#         data.get("vehicle_type", "None"),
#         data.get("vehicle_number", ""),
#         data["entry_date"],
#         data["expiry_date"],
#         data["created_by"],
#     )

#     result = run_query(sql, params)

#     if result:
#         print(f"[TICKET] Saved: {data['full_name']} → {ticket_number}")
#         return ticket_number
#     else:
#         print(f"[TICKET] Failed to save: {data['full_name']}")
#         return None


# def get_tourist_by_ticket(ticket_number):
#     rows = run_query(
#         "SELECT * FROM tourists WHERE ticket_number = %s",
#         (ticket_number,),
#         fetch=True
#     )
#     return rows[0] if rows else None


# def get_tourist_checkpost_history(ticket_number):
#     return run_query(
#         """SELECT checkpost_name, officer_name, scan_time, status
#            FROM checkpost_logs
#            WHERE ticket_number = %s
#            ORDER BY scan_time ASC""",
#         (ticket_number,),
#         fetch=True
#     ) or []


# def calculate_expiry(entry_date=None, days=None):
#     if entry_date is None:
#         entry_date = date.today()
#     if days is None:
#         days = TICKET_VALIDITY_DAYS
#     return entry_date + timedelta(days=days)


# if __name__ == "__main__":
#     print("Next ticket number:", generate_ticket_number())
# modules/ticket_creator.py
# ============================================================
# Handles saving tourists to DB using the NEW schema.
# New schema columns used here:
#   first_name, mid_name, last_name, dob, gender,
#   country_id, occupation_id, purpose_id, region_id,
#   entry_post_id, exit_post_id, entry_date, expiry_date,
#   guide_name, guide_contact, guide_total, guide_trained,
#   porter_name, porter_contact, porter_total,
#   photo_path, passport_number, email_address, contact_number,
#   permanent_address, fee, payment_method, fiscal_year,
#   agent_id, agent_org_id, status, created_by, created_at
# ============================================================

import sys
import os
from datetime import date, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from config import TICKET_PREFIX, TICKET_VALIDITY_DAYS
from database.local_db import run_query


# ─────────────────────────────────────────
# LOOKUP HELPERS  (id ↔ name)
# ─────────────────────────────────────────

def get_country_id(country_name):
    """Return countries.id for a given country name string."""
    rows = run_query(
        "SELECT id FROM countries WHERE name = %s AND status = 1 LIMIT 1",
        (country_name,), fetch=True
    )
    return rows[0]["id"] if rows else None


def get_occupation_id(occupation_name):
    """Return occupations.id for a given occupation name string."""
    rows = run_query(
        "SELECT id FROM occupations WHERE name = %s AND status = 1 LIMIT 1",
        (occupation_name,), fetch=True
    )
    return rows[0]["id"] if rows else None


def get_purpose_id(purpose_name):
    """Return purposes.id for Trekking / Tourism / Research."""
    rows = run_query(
        "SELECT id FROM purposes WHERE name = %s AND status = 1 LIMIT 1",
        (purpose_name,), fetch=True
    )
    return rows[0]["id"] if rows else None


def get_region_id(region_name):
    """Return trekking_regions.id for a region name."""
    rows = run_query(
        "SELECT id FROM trekking_regions WHERE name = %s AND status = 1 LIMIT 1",
        (region_name,), fetch=True
    )
    return rows[0]["id"] if rows else None


def get_checkpost_id(checkpost_name):
    """Return checkposts.id for a checkpost name."""
    rows = run_query(
        "SELECT id FROM checkposts WHERE name = %s AND is_active = 1 LIMIT 1",
        (checkpost_name,), fetch=True
    )
    return rows[0]["id"] if rows else None


# ─────────────────────────────────────────
# DROPDOWN DATA  (for UI to populate lists)
# ─────────────────────────────────────────

def fetch_countries():
    """Returns list of country names for the UI dropdown."""
    rows = run_query(
        "SELECT name FROM countries WHERE status = 1 ORDER BY name ASC",
        fetch=True
    )
    return [r["name"] for r in rows] if rows else []


def fetch_occupations():
    """Returns list of occupation names for the UI dropdown."""
    rows = run_query(
        "SELECT name FROM occupations WHERE status = 1 ORDER BY name ASC",
        fetch=True
    )
    return [r["name"] for r in rows] if rows else []


def fetch_purposes():
    """Returns list of purpose names (Trekking / Tourism / Research)."""
    rows = run_query(
        "SELECT name FROM purposes WHERE status = 1 ORDER BY name ASC",
        fetch=True
    )
    return [r["name"] for r in rows] if rows else ["Trekking", "Tourism", "Research"]


def fetch_regions():
    """Returns list of trekking region names for the UI dropdown."""
    rows = run_query(
        "SELECT name FROM trekking_regions WHERE status = 1 ORDER BY name ASC",
        fetch=True
    )
    return [r["name"] for r in rows] if rows else []


def fetch_checkposts():
    """Returns list of checkpost names for entry/exit dropdowns."""
    rows = run_query(
        "SELECT name FROM checkposts WHERE is_active = 1 ORDER BY name ASC",
        fetch=True
    )
    return [r["name"] for r in rows] if rows else []


# ─────────────────────────────────────────
# TICKET NUMBER GENERATOR
# ─────────────────────────────────────────

def generate_ticket_number():
    """
    Generates next ticket number e.g. NPL-2026-00001
    Looks at the last ticket in the DB for the current year.
    """
    year = date.today().year
    rows = run_query(
        "SELECT ticket_number FROM tourists WHERE ticket_number LIKE %s ORDER BY id DESC LIMIT 1",
        (f"{TICKET_PREFIX}-{year}-%",),
        fetch=True
    )
    if rows:
        last_ticket = rows[0]["ticket_number"]
        last_number = int(last_ticket.split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{TICKET_PREFIX}-{year}-{next_number:05d}"


# ─────────────────────────────────────────
# SAVE TOURIST  (main function)
# ─────────────────────────────────────────

def save_tourist(data):
    """
    Saves one tourist to the DB using the new schema.
    
    Expected keys in `data`:
        first_name, mid_name (optional), last_name
        dob, gender (Male/Female/Other)
        country        → will be looked up to country_id
        occupation     → will be looked up to occupation_id
        purpose        → Trekking / Tourism / Research
        region         → trekking region name
        entry_point    → checkpost name
        exit_point     → checkpost name
        passport_number, photo_path (optional)
        email_address (optional), contact_number (optional)
        permanent_address (optional)
        entry_date, expiry_date
        guide_name, guide_contact, guide_total, guide_trained (0/1)
        porter_name, porter_contact, porter_total
        fee (optional), payment_method (optional)
        fiscal_year (optional)
        created_by     → officer username

    Returns ticket_number string on success, None on failure.
    """
    ticket_number = generate_ticket_number()

    # ── Resolve FK ids ──────────────────────────────
    def get_country_id(conn, name):
     cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM countries WHERE name = %s OR nationality = %s LIMIT 1",
        (name, name)
    )
    row = cursor.fetchone()
    return row[0] if row else None
    occupation_id = get_occupation_id(data.get("occupation", ""))
    purpose_id    = get_purpose_id(data.get("purpose", "Trekking"))
    region_id     = get_region_id(data.get("region", ""))
    entry_post_id = get_checkpost_id(data.get("entry_point", ""))
    exit_post_id  = get_checkpost_id(data.get("exit_point", ""))

    # gender: store single letter M/F/O
    gender_map = {"Male": "M", "Female": "F", "Other": "O"}
    gender = gender_map.get(data.get("gender", ""), "O")

    sql = """
        INSERT INTO tourists (
            ticket_number,
            first_name, mid_name, last_name,
            dob, gender,
            country_id, nationality,
            occupation_id,
            purpose_id,
            region_id,
            entry_post_id, exit_post_id,
            passport_number, photo_path,
            email_address, contact_number, permanent_address,
            entry_date, expiry_date,
            guide_name, guide_contact, guide_total, guide_trained,
            porter_name, porter_contact, porter_total,
            fee, payment_method, fiscal_year,
            status, created_by, applied_at
        ) VALUES (
            %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s,
            %s,
            %s,
            %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
        )
    """

    params = (
        ticket_number,
        # name
        data.get("first_name", ""),
        data.get("mid_name", None),
        data.get("last_name", ""),
        # personal
        data.get("dob", None),
        gender,
        # country
        country_id,
        data.get("country", ""),       # store raw nationality string too
        # occupation, purpose, region
        occupation_id,
        purpose_id,
        region_id,
        # checkposts
        entry_post_id,
        exit_post_id,
        # document
        data.get("passport_number", ""),
        data.get("photo_path", None),
        # contact
        data.get("email_address", None),
        data.get("contact_number", None),
        data.get("permanent_address", None),
        # dates
        data.get("entry_date", None),
        data.get("expiry_date", None),
        # guide
        data.get("guide_name", None),
        data.get("guide_contact", None),
        data.get("guide_total", None),
        data.get("guide_trained", None),
        # porter
        data.get("porter_name", None),
        data.get("porter_contact", None),
        data.get("porter_total", None),
        # payment
        data.get("fee", None),
        data.get("payment_method", None),
        data.get("fiscal_year", None),
        # status: 1 = Applied
        1,
        data.get("created_by", ""),
        date.today(),
    )

    result = run_query(sql, params)

    if result:
        print(f"[TICKET] Saved: {data.get('first_name')} {data.get('last_name')} → {ticket_number}")
        return ticket_number
    else:
        print(f"[TICKET] Failed to save: {data.get('first_name')} {data.get('last_name')}")
        return None


# ─────────────────────────────────────────
# READ HELPERS
# ─────────────────────────────────────────

def get_tourist_by_ticket(ticket_number):
    """Fetch full tourist row by ticket number."""
    rows = run_query(
        """
        SELECT t.*,
               c.name  AS country_name,
               c.is_saarc,
               o.name  AS occupation_name,
               p.name  AS purpose_name,
               r.name  AS region_name,
               ep.name AS entry_post_name,
               xp.name AS exit_post_name
        FROM tourists t
        LEFT JOIN countries       c  ON t.country_id    = c.id
        LEFT JOIN occupations     o  ON t.occupation_id = o.id
        LEFT JOIN purposes        p  ON t.purpose_id    = p.id
        LEFT JOIN trekking_regions r ON t.region_id     = r.id
        LEFT JOIN checkposts      ep ON t.entry_post_id = ep.id
        LEFT JOIN checkposts      xp ON t.exit_post_id  = xp.id
        WHERE t.ticket_number = %s
        """,
        (ticket_number,),
        fetch=True
    )
    return rows[0] if rows else None


def get_tourist_checkpost_history(ticket_number):
    """Get all checkpost scan logs for a given ticket."""
    rows = run_query(
        """
        SELECT cp.name AS checkpost_name,
               o.full_name AS officer_name,
               cl.scan_time, cl.status, cl.notes
        FROM checkpost_logs cl
        LEFT JOIN checkposts cp ON cl.checkpost_id = cp.id
        LEFT JOIN officers   o  ON cl.officer_id   = o.id
        JOIN tourists t ON cl.tourist_id = t.id
        WHERE t.ticket_number = %s
        ORDER BY cl.scan_time ASC
        """,
        (ticket_number,),
        fetch=True
    )
    return rows or []


def calculate_expiry(entry_date=None, days=None):
    if entry_date is None:
        entry_date = date.today()
    if days is None:
        days = TICKET_VALIDITY_DAYS
    return entry_date + timedelta(days=days)


# ─────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Next ticket number:", generate_ticket_number())