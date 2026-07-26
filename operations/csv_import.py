"""CSV import for job runs — bridge for Control-M exports / parsed alert mails.

Columns (case-insensitive): job_name, run_date, status, remarks.
Unknown jobs are auto-created (category OTHER) so a raw export can bootstrap
the job master.
"""
import csv
import io
from datetime import datetime

from .models import BatchJob, JobRun

DATE_FORMATS = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"]

STATUS_MAP = {
    "success": "SUCCESS", "ok": "SUCCESS", "ended ok": "SUCCESS", "completed": "SUCCESS",
    "failed": "FAILED", "failure": "FAILED", "ended notok": "FAILED", "notok": "FAILED",
    "abended": "FAILED", "error": "FAILED",
    "running": "RUNNING", "executing": "RUNNING", "in progress": "RUNNING",
    "skipped": "SKIPPED", "not run": "SKIPPED", "hold": "SKIPPED", "cancelled": "SKIPPED",
}


def _parse_date(value):
    value = (value or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def import_runs(uploaded_file, user=None):
    """Returns (imported, jobs_created, errors)."""
    text = uploaded_file.read().decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return 0, 0, ["Empty file."]
    fmap = {n.strip().lower(): n for n in reader.fieldnames}

    def get(row, key):
        src = fmap.get(key)
        return (row.get(src) or "").strip() if src else ""

    for required in ("job_name", "run_date", "status"):
        if required not in fmap:
            return 0, 0, [f"Missing required column: {required}"]

    imported = jobs_created = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        name = get(row, "job_name")
        if not name:
            continue
        run_date = _parse_date(get(row, "run_date"))
        status = STATUS_MAP.get(get(row, "status").lower(), get(row, "status").upper())
        if not run_date:
            errors.append(f"Row {i} ({name}): bad run_date — skipped.")
            continue
        if status not in JobRun.Status.values:
            errors.append(f"Row {i} ({name}): unknown status '{get(row, 'status')}' — skipped.")
            continue
        job, created = BatchJob.objects.get_or_create(
            name=name, defaults={"category": BatchJob.Category.OTHER}
        )
        if created:
            jobs_created += 1
        JobRun.objects.update_or_create(
            job=job, run_date=run_date,
            defaults={"status": status, "remarks": get(row, "remarks"), "updated_by": user},
        )
        imported += 1
    return imported, jobs_created, errors
