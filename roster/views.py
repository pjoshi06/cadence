from collections import Counter
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import Profile
from leaves.models import LeaveRequest

from .forms import ShiftForm
from .models import Shift, ShiftAssignment


def _is_manager(user):
    return hasattr(user, "profile") and user.profile.is_approver


def _week_start(request):
    raw = request.GET.get("start") or request.POST.get("start") or ""
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        d = date.today()
    return d - timedelta(days=d.weekday())


def _cell_context(member, day, shifts, can_edit):
    assignment = ShiftAssignment.objects.filter(user=member, date=day).select_related("shift").first()
    on_leave = LeaveRequest.objects.filter(
        user=member, status=LeaveRequest.Status.APPROVED,
        start_date__lte=day, end_date__gte=day,
    ).exists()
    return {
        "member": member, "day": day, "assignment": assignment,
        "on_leave": on_leave, "shifts": shifts, "can_edit": can_edit,
    }


@login_required
def roster_week(request):
    Shift.ensure_defaults()
    start = _week_start(request)
    days = [start + timedelta(days=i) for i in range(7)]
    shifts = list(Shift.objects.filter(is_active=True))
    can_edit = _is_manager(request.user)

    members = [p.user for p in
               Profile.objects.filter(user__is_active=True).select_related("user")
               .order_by("user__first_name")]

    assignments = {
        (a.user_id, a.date): a
        for a in ShiftAssignment.objects.filter(date__range=(days[0], days[-1]))
        .select_related("shift")
    }
    leaves = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=days[-1], end_date__gte=days[0],
    )

    rows = []
    for member in members:
        cells = []
        for day in days:
            on_leave = any(
                lv.user_id == member.id and lv.start_date <= day <= lv.end_date
                for lv in leaves
            )
            cells.append({
                "member": member, "day": day,
                "assignment": assignments.get((member.id, day)),
                "on_leave": on_leave,
                "shifts": shifts, "can_edit": can_edit,
            })
        rows.append({"member": member, "cells": cells})

    coverage = []
    for i, day in enumerate(days):
        counts = Counter()
        for row in rows:
            a = row["cells"][i]["assignment"]
            if a:
                counts[a.shift] += 1
        coverage.append([
            {"shift": s, "count": n}
            for s, n in sorted(counts.items(), key=lambda kv: kv[0].code)
        ])

    return render(request, "roster/roster_week.html", {
        "days": days,
        "rows": rows,
        "shifts": shifts,
        "coverage": coverage,
        "can_edit": can_edit,
        "week_start": start,
        "week_end": days[-1],
        "prev_start": (start - timedelta(days=7)).isoformat(),
        "next_start": (start + timedelta(days=7)).isoformat(),
        "today": date.today(),
    })


@login_required
def set_shift(request):
    if request.method != "POST" or not _is_manager(request.user):
        return redirect("roster_week")
    member = get_object_or_404(Profile, user_id=request.POST.get("user_id")).user
    day = date.fromisoformat(request.POST.get("date"))
    shift_id = request.POST.get("shift") or ""
    if shift_id:
        shift = get_object_or_404(Shift, pk=shift_id)
        ShiftAssignment.objects.update_or_create(
            user=member, date=day, defaults={"shift": shift}
        )
    else:
        ShiftAssignment.objects.filter(user=member, date=day).delete()
    shifts = list(Shift.objects.filter(is_active=True))
    return render(request, "roster/_cell.html",
                  {"cell": _cell_context(member, day, shifts, True)})


@login_required
def shift_list(request):
    Shift.ensure_defaults()
    shifts = Shift.objects.all().order_by("-is_active", "start_time", "code")
    return render(request, "roster/shift_list.html", {
        "shifts": shifts,
        "can_edit": _is_manager(request.user),
    })


@login_required
def shift_form(request, pk=None):
    if not _is_manager(request.user):
        messages.error(request, "Only managers can manage shifts.")
        return redirect("shift_list")
    instance = get_object_or_404(Shift, pk=pk) if pk else None
    form = ShiftForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        shift = form.save()
        messages.success(request, f'Shift "{shift.code} · {shift.name}" saved.')
        return redirect("shift_list")
    return render(request, "roster/shift_form.html", {"form": form, "instance": instance})


@login_required
def shift_delete(request, pk):
    if not _is_manager(request.user) or request.method != "POST":
        return redirect("shift_list")
    shift = get_object_or_404(Shift, pk=pk)
    used = shift.assignments.count()
    if used:
        shift.is_active = False
        shift.save(update_fields=["is_active"])
        messages.warning(
            request,
            f'"{shift.code}" is used in {used} roster entr{"ies" if used != 1 else "y"} — '
            "it was deactivated instead of deleted, so history is preserved.",
        )
    else:
        shift.delete()
        messages.success(request, f'Shift "{shift.code}" deleted.')
    return redirect("shift_list")


@login_required
def copy_prev_week(request):
    if request.method != "POST" or not _is_manager(request.user):
        return redirect("roster_week")
    start = _week_start(request)
    days = [start + timedelta(days=i) for i in range(7)]
    prev_days = [d - timedelta(days=7) for d in days]
    copied = 0
    for a in ShiftAssignment.objects.filter(date__range=(prev_days[0], prev_days[-1])):
        _, created = ShiftAssignment.objects.get_or_create(
            user=a.user, date=a.date + timedelta(days=7), defaults={"shift": a.shift}
        )
        if created:
            copied += 1
    messages.success(request, f"Copied {copied} assignment{'s' if copied != 1 else ''} from last week (existing entries kept).")
    return redirect(f"{reverse('roster_week')}?start={start.isoformat()}")
