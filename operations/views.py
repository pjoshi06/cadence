from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .csv_import import import_runs
from .forms import BatchJobForm, RunCSVForm
from .models import BatchJob, JobRun

SAMPLE_CSV = """job_name,run_date,status,remarks
DWH_NIGHTLY_LOAD,2026-07-25,Success,
FIN_INTERFACE_SAP,2026-07-25,Failed,Connection timeout - INC0012399
INFRA_BACKUP_PROD,2026-07-25,Running,
"""


def _is_manager(user):
    return hasattr(user, "profile") and user.profile.is_approver


def _cell(job, day, run):
    return {"job": job, "day": day, "run": run, "statuses": JobRun.Status.choices}


@login_required
def job_board(request):
    today = date.today()
    try:
        end = date.fromisoformat(request.GET.get("end", ""))
    except ValueError:
        end = today
    days = [end - timedelta(days=i) for i in range(6, -1, -1)]

    jobs = BatchJob.objects.filter(is_active=True)
    category = request.GET.get("category", "")
    if category:
        jobs = jobs.filter(category=category)

    runs = {
        (r.job_id, r.run_date): r
        for r in JobRun.objects.filter(run_date__range=(days[0], days[-1]))
        .select_related("job")
    }

    rows = []
    for job in jobs:
        cells = [_cell(job, d, runs.get((job.id, d))) for d in days]
        rows.append({"job": job, "cells": cells})

    todays = {s: 0 for s, _ in JobRun.Status.choices}
    pending = 0
    failures_today = []
    for row in rows:
        run = runs.get((row["job"].id, end))
        if run:
            todays[run.status] += 1
            if run.status == JobRun.Status.FAILED:
                failures_today.append(run)
        else:
            pending += 1

    return render(request, "operations/job_board.html", {
        "rows": rows,
        "days": days,
        "board_end": end,
        "is_today": end == today,
        "prev_end": (end - timedelta(days=7)).isoformat(),
        "next_end": (end + timedelta(days=7)).isoformat(),
        "today": today,
        "todays": todays,
        "pending": pending,
        "failures_today": failures_today,
        "sel_category": category,
        "categories": BatchJob.Category.choices,
        "csv_form": RunCSVForm(),
        "can_manage": _is_manager(request.user),
    })


@login_required
def run_set(request):
    if request.method != "POST":
        return redirect("job_board")
    job = get_object_or_404(BatchJob, pk=request.POST.get("job_id"))
    day = date.fromisoformat(request.POST.get("date"))
    status = request.POST.get("status") or ""
    remarks = request.POST.get("remarks", "")
    if status in JobRun.Status.values:
        run, _ = JobRun.objects.update_or_create(
            job=job, run_date=day,
            defaults={"status": status, "updated_by": request.user,
                      **({"remarks": remarks} if remarks else {})},
        )
    else:
        JobRun.objects.filter(job=job, run_date=day).delete()
        run = None
    return render(request, "operations/_run_cell.html", {"cell": _cell(job, day, run)})


@login_required
def mark_rest_success(request):
    if request.method != "POST":
        return redirect("job_board")
    day = date.fromisoformat(request.POST.get("date"))
    done = JobRun.objects.filter(run_date=day).values_list("job_id", flat=True)
    created = 0
    for job in BatchJob.objects.filter(is_active=True).exclude(id__in=done):
        JobRun.objects.create(job=job, run_date=day, status=JobRun.Status.SUCCESS,
                              updated_by=request.user)
        created += 1
    messages.success(request, f"Marked {created} remaining job{'s' if created != 1 else ''} as Success for {day.strftime('%d %b')}.")
    return redirect(f"{reverse('job_board')}?end={day.isoformat()}")


@login_required
def run_import(request):
    if request.method == "POST":
        form = RunCSVForm(request.POST, request.FILES)
        if form.is_valid():
            imported, jobs_created, errors = import_runs(form.cleaned_data["file"], request.user)
            msg = f"Imported {imported} run{'s' if imported != 1 else ''}."
            if jobs_created:
                msg += f" {jobs_created} new job{'s' if jobs_created != 1 else ''} auto-created (category: Other)."
            messages.success(request, msg)
            for err in errors[:5]:
                messages.warning(request, err)
    return redirect("job_board")


@login_required
def sample_run_csv(request):
    response = HttpResponse(SAMPLE_CSV, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="job_runs_sample.csv"'
    return response


@login_required
def job_master(request):
    jobs = BatchJob.objects.all().order_by("-is_active", "category", "name")
    return render(request, "operations/job_master.html", {
        "jobs": jobs,
        "can_manage": _is_manager(request.user),
    })


@login_required
def job_form(request, pk=None):
    if not _is_manager(request.user):
        messages.error(request, "Only managers can manage the job master.")
        return redirect("job_master")
    instance = get_object_or_404(BatchJob, pk=pk) if pk else None
    form = BatchJobForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        job = form.save()
        messages.success(request, f'Job "{job.name}" saved.')
        return redirect("job_master")
    return render(request, "operations/job_form.html", {"form": form, "instance": instance})


@login_required
def job_toggle(request, pk):
    if request.method == "POST" and _is_manager(request.user):
        job = get_object_or_404(BatchJob, pk=pk)
        job.is_active = not job.is_active
        job.save(update_fields=["is_active"])
        state = "re-activated" if job.is_active else "deactivated"
        messages.success(request, f'Job "{job.name}" {state}.')
    return redirect("job_master")
