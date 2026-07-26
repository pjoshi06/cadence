from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from leaves.models import LeaveRequest
from operations.models import BatchJob, JobRun
from reports.models import GeneratedReport, Ticket
from workboard.models import Task

from .forms import MemberForm
from .models import Profile


def _is_manager(user):
    return hasattr(user, "profile") and user.profile.is_approver


@login_required
def dashboard(request):
    today = date.today()
    week_ago = today - timedelta(days=7)

    open_tickets = Ticket.objects.exclude(state__in=["Resolved", "Closed", "Cancelled"]).count()
    resolved_week = Ticket.objects.filter(resolved_at__date__gte=week_ago).count()
    sla_total = Ticket.objects.filter(resolved_at__isnull=False).count()
    sla_met = Ticket.objects.filter(resolved_at__isnull=False, sla_met=True).count()
    sla_pct = round(sla_met / sla_total * 100, 1) if sla_total else None

    on_leave_today = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED, start_date__lte=today, end_date__gte=today
    ).select_related("user")

    my_tasks = (
        Task.objects.filter(assignee=request.user)
        .exclude(status=Task.Status.DONE)
        .order_by("due_date")[:6]
    )

    pending_leaves = 0
    if _is_manager(request.user):
        pending_leaves = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count()

    workload = (
        Profile.objects.select_related("user")
        .annotate(
            open_tasks=Count(
                "user__tasks",
                filter=~Q(user__tasks__status=Task.Status.DONE),
            )
        )
        .order_by("-open_tasks")
    )
    max_load = max([w.open_tasks for w in workload], default=0) or 1

    priority_counts = (
        Ticket.objects.exclude(state__in=["Resolved", "Closed", "Cancelled"])
        .values("priority")
        .annotate(n=Count("id"))
    )
    priority_map = {p["priority"]: p["n"] for p in priority_counts}

    recent_reports = GeneratedReport.objects.select_related("created_by")[:5]

    total_jobs = BatchJob.objects.filter(is_active=True).count()
    runs_today = JobRun.objects.filter(run_date=today, job__is_active=True)
    jobs_failed = runs_today.filter(status=JobRun.Status.FAILED).count()
    jobs_success = runs_today.filter(status=JobRun.Status.SUCCESS).count()
    jobs_pending = total_jobs - runs_today.count()

    return render(request, "dashboard.html", {
        "open_tickets": open_tickets,
        "resolved_week": resolved_week,
        "sla_pct": sla_pct,
        "on_leave_today": on_leave_today,
        "my_tasks": my_tasks,
        "pending_leaves": pending_leaves,
        "workload": workload,
        "max_load": max_load,
        "priority_map": priority_map,
        "recent_reports": recent_reports,
        "total_jobs": total_jobs,
        "jobs_failed": jobs_failed,
        "jobs_success": jobs_success,
        "jobs_pending": jobs_pending,
        "today": today,
    })


@login_required
def team_list(request):
    members = Profile.objects.select_related("user").order_by("user__first_name")
    return render(request, "accounts/team_list.html", {"members": members})


@login_required
def member_form(request, pk=None):
    if not _is_manager(request.user):
        messages.error(request, "Only managers can manage team members.")
        return redirect("team_list")
    instance = get_object_or_404(Profile, pk=pk) if pk else None
    form = MemberForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Team member saved.")
        return redirect("team_list")
    return render(request, "accounts/member_form.html", {"form": form, "instance": instance})


@login_required
def member_toggle_active(request, pk):
    if not _is_manager(request.user) or request.method != "POST":
        return redirect("team_list")
    profile = get_object_or_404(Profile, pk=pk)
    profile.user.is_active = not profile.user.is_active
    profile.user.save(update_fields=["is_active"])
    state = "re-activated" if profile.user.is_active else "deactivated"
    messages.success(request, f"{profile.user.get_full_name() or profile.user.username} {state}.")
    return redirect("team_list")
