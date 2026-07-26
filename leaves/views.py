import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LeaveRequestForm
from .models import LeaveRequest


def _is_approver(user):
    return hasattr(user, "profile") and user.profile.is_approver


@login_required
def leave_list(request):
    my_leaves = LeaveRequest.objects.filter(user=request.user)
    pending = None
    if _is_approver(request.user):
        pending = (
            LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING)
            .exclude(user=request.user)
            .select_related("user")
        )

    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)
    approved = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=month_days[-1][-1],
        end_date__gte=month_days[0][0],
    ).select_related("user")

    month_grid = []
    for week in month_days:
        row = []
        for d in week:
            day_leaves = [lv for lv in approved if lv.start_date <= d <= lv.end_date]
            row.append({
                "date": d,
                "in_month": d.month == month,
                "is_today": d == today,
                "leaves": day_leaves,
            })
        month_grid.append(row)

    prev_month = (month - 2) % 12 + 1
    prev_year = year - 1 if month == 1 else year
    next_month = month % 12 + 1
    next_year = year + 1 if month == 12 else year

    return render(request, "leaves/leave_list.html", {
        "my_leaves": my_leaves,
        "pending": pending,
        "month_grid": month_grid,
        "cal_year": year,
        "cal_month": month,
        "cal_month_name": calendar.month_name[month],
        "prev_month": prev_month, "prev_year": prev_year,
        "next_month": next_month, "next_year": next_year,
        "today": today,
    })


@login_required
def leave_apply(request):
    form = LeaveRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        leave = form.save(commit=False)
        leave.user = request.user
        leave.save()
        messages.success(request, "Leave request submitted for approval.")
        return redirect("leave_list")
    return render(request, "leaves/leave_form.html", {"form": form})


@login_required
def leave_decide(request, pk, decision):
    if not _is_approver(request.user) or request.method != "POST":
        return redirect("leave_list")
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if decision == "approve":
        leave.status = LeaveRequest.Status.APPROVED
    else:
        leave.status = LeaveRequest.Status.REJECTED
    leave.approver = request.user
    leave.decided_at = timezone.now()
    leave.save()
    return render(request, "leaves/_pending_row.html", {"lv": leave, "decided": True})


@login_required
def leave_cancel(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk, user=request.user)
    if request.method == "POST" and leave.status == LeaveRequest.Status.PENDING:
        leave.status = LeaveRequest.Status.CANCELLED
        leave.save(update_fields=["status"])
        messages.success(request, "Leave request cancelled.")
    return redirect("leave_list")
