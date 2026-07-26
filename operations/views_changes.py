from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ChangeRequestForm
from .models import ChangeEvent, ChangeRequest


def _next_actions(cr):
    """Contextual primary actions for the current state."""
    kinds = set(cr.events.values_list("kind", flat=True))
    actions = []
    if not cr.is_open:
        return actions
    if "RUNBOOK_RECEIVED" not in kinds:
        actions.append(("RUNBOOK_RECEIVED", "Runbook received"))
    if "WT_HELD" not in kinds:
        if "WT_SCHEDULED" not in kinds:
            actions.append(("WT_SCHEDULED", "Schedule walkthrough"))
        else:
            actions.append(("WT_SCHEDULED", "Reschedule walkthrough"))
            actions.append(("WT_HELD", "Walkthrough held"))
    if "REVIEW_1" not in kinds:
        actions.append(("REVIEW_1", "Send first review"))
    elif "REVIEW_2" not in kinds:
        actions.append(("REVIEW_2", "Send second review"))
    return actions


@login_required
def change_list(request):
    changes = ChangeRequest.objects.select_related("reviewer")
    state = request.GET.get("state", "open")
    if state == "open":
        changes = changes.filter(status__in=ChangeRequest.OPEN_STATUSES)
    elif state == "closed":
        changes = changes.exclude(status__in=ChangeRequest.OPEN_STATUSES)

    open_count = ChangeRequest.objects.filter(status__in=ChangeRequest.OPEN_STATUSES).count()
    decided = ChangeRequest.objects.exclude(status__in=ChangeRequest.OPEN_STATUSES)
    turnarounds = [c.first_review_turnaround_days for c in
                   ChangeRequest.objects.all() if c.first_review_turnaround_days is not None]
    avg_turnaround = round(sum(turnarounds) / len(turnarounds), 1) if turnarounds else None

    return render(request, "operations/change_list.html", {
        "changes": changes,
        "today": timezone.localdate(),
        "sel_state": state,
        "open_count": open_count,
        "approved_count": decided.filter(status="APPROVED").count(),
        "avg_turnaround": avg_turnaround,
    })


@login_required
def change_form(request, pk=None):
    instance = get_object_or_404(ChangeRequest, pk=pk) if pk else None
    form = ChangeRequestForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        cr = form.save(commit=False)
        creating = not cr.pk
        if creating:
            cr.created_by = request.user
        cr.save()
        if creating:
            ChangeEvent.objects.create(change=cr, kind=ChangeEvent.Kind.CREATED,
                                       by=request.user)
            if form.cleaned_data.get("runbook_already_received"):
                ChangeEvent.objects.create(change=cr,
                                           kind=ChangeEvent.Kind.RUNBOOK_RECEIVED,
                                           by=request.user)
        messages.success(request, f"Change {cr.cr_number} saved.")
        return redirect("change_detail", pk=cr.pk)
    return render(request, "operations/change_form.html", {"form": form, "instance": instance})


@login_required
def change_detail(request, pk):
    cr = get_object_or_404(ChangeRequest.objects.select_related("reviewer", "created_by"), pk=pk)
    return render(request, "operations/change_detail.html", {
        "cr": cr,
        "events": cr.events.select_related("by"),
        "next_actions": _next_actions(cr),
    })


@login_required
def change_action(request, pk):
    cr = get_object_or_404(ChangeRequest, pk=pk)
    if request.method != "POST":
        return redirect("change_detail", pk=pk)
    kind = request.POST.get("kind", "")
    if kind not in ChangeEvent.Kind.values:
        messages.error(request, "Unknown action.")
        return redirect("change_detail", pk=pk)

    scheduled_for = None
    raw = request.POST.get("scheduled_for", "").strip()
    if raw:
        try:
            scheduled_for = timezone.make_aware(datetime.fromisoformat(raw))
        except ValueError:
            scheduled_for = None

    ChangeEvent.objects.create(
        change=cr, kind=kind, note=request.POST.get("note", "").strip(),
        scheduled_for=scheduled_for, by=request.user,
    )
    new_status = ChangeEvent.STATUS_MAP.get(kind)
    if new_status:
        cr.status = new_status
        cr.save(update_fields=["status"])
    label = dict(ChangeEvent.Kind.choices)[kind]
    messages.success(request, f"{cr.cr_number}: {label} recorded.")
    return redirect("change_detail", pk=pk)
