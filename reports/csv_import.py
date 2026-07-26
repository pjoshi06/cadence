"""CSV import for ticket data — stands in for the ServiceNow API feed.

Expected columns (header names are matched case-insensitively):
number, short_description, priority, state, opened_at, resolved_at,
assigned_to, assignment_group, category, sla_met
"""
import csv
import io
from datetime import datetime

from django.utils import timezone

from .models import Ticket

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y",
]


def _parse_dt(value):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return timezone.make_aware(dt, timezone.get_current_timezone())
        except ValueError:
            continue
    return None


def _norm_priority(value):
    value = (value or "").strip().upper()
    if value.startswith("P") and len(value) >= 2 and value[1] in "1234":
        return value[:2]
    for digit in "1234":
        if value.startswith(digit):
            return f"P{digit}"
    mapping = {"CRITICAL": "P1", "HIGH": "P2", "MODERATE": "P3", "MEDIUM": "P3", "LOW": "P4"}
    return mapping.get(value, "P3")


def _norm_bool(value):
    value = (value or "").strip().lower()
    if value in ("true", "yes", "y", "1", "met"):
        return True
    if value in ("false", "no", "n", "0", "missed", "breached"):
        return False
    return None


def import_tickets(uploaded_file):
    """Returns (created, updated, errors:list[str])."""
    raw = uploaded_file.read()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return 0, 0, ["Empty file."]
    field_map = {name.strip().lower(): name for name in reader.fieldnames}

    def get(row, key):
        src = field_map.get(key)
        return (row.get(src) or "").strip() if src else ""

    if "number" not in field_map:
        return 0, 0, ["Missing required column: number"]

    created = updated = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        number = get(row, "number")
        if not number:
            continue
        opened_at = _parse_dt(get(row, "opened_at"))
        if not opened_at:
            errors.append(f"Row {i} ({number}): missing/unparseable opened_at — skipped.")
            continue
        defaults = {
            "short_description": get(row, "short_description") or "(no description)",
            "priority": _norm_priority(get(row, "priority")),
            "state": get(row, "state") or "New",
            "opened_at": opened_at,
            "resolved_at": _parse_dt(get(row, "resolved_at")),
            "assigned_to": get(row, "assigned_to"),
            "assignment_group": get(row, "assignment_group"),
            "category": get(row, "category"),
            "sla_met": _norm_bool(get(row, "sla_met")),
        }
        _, was_created = Ticket.objects.update_or_create(number=number, defaults=defaults)
        if was_created:
            created += 1
        else:
            updated += 1
    return created, updated, errors
