# modules/ticket_creator.py
import sys
import os
from datetime import date, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from config import TICKET_PREFIX, TICKET_VALIDITY_DAYS
from database.local_db import run_query


def generate_ticket_number():
    """
    Generates next ticket number e.g. NPL-2026-00001
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


def save_tourist(data):
    """
    Saves tourist to DB. Returns ticket_number on success, None on failure.
    """
    # Generate ticket number FIRST before using it
    ticket_number = generate_ticket_number()

    sql = """
        INSERT INTO tourists (
            ticket_number, full_name, passport_number,
            nationality, photo_path, visa_type,
            vehicle_type, vehicle_number,
            entry_date, expiry_date, created_by
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    params = (
        ticket_number,
        data["full_name"],
        data["passport_number"],
        data["nationality"],
        data.get("photo_path", None),
        data["visa_type"],
        data.get("vehicle_type", "None"),
        data.get("vehicle_number", ""),
        data["entry_date"],
        data["expiry_date"],
        data["created_by"],
    )

    result = run_query(sql, params)

    if result:
        print(f"[TICKET] Saved: {data['full_name']} → {ticket_number}")
        return ticket_number
    else:
        print(f"[TICKET] Failed to save: {data['full_name']}")
        return None


def get_tourist_by_ticket(ticket_number):
    rows = run_query(
        "SELECT * FROM tourists WHERE ticket_number = %s",
        (ticket_number,),
        fetch=True
    )
    return rows[0] if rows else None


def get_tourist_checkpost_history(ticket_number):
    return run_query(
        """SELECT checkpost_name, officer_name, scan_time, status
           FROM checkpost_logs
           WHERE ticket_number = %s
           ORDER BY scan_time ASC""",
        (ticket_number,),
        fetch=True
    ) or []


def calculate_expiry(entry_date=None, days=None):
    if entry_date is None:
        entry_date = date.today()
    if days is None:
        days = TICKET_VALIDITY_DAYS
    return entry_date + timedelta(days=days)


if __name__ == "__main__":
    print("Next ticket number:", generate_ticket_number())