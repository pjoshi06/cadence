from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task


def _can_view_all(user):
    return hasattr(user, "profile") and user.profile.is_approver


def _can_touch(user, task):
    """Members may only act on tasks assigned to them (or that they created)."""
    return _can_view_all(user) or task.assignee_id == user.id or task.created_by_id == user.id


@login_required
def task_list(request):
    can_view_all = _can_view_all(request.user)
    tasks = Task.objects.select_related("assignee").all()
    assignee = request.GET.get("assignee", "")
    status = request.GET.get("status", "")

    if not can_view_all:
        tasks = tasks.filter(assignee=request.user)
        assignee = "me"
    elif assignee == "me":
        tasks = tasks.filter(assignee=request.user)
    elif assignee.isdigit():
        tasks = tasks.filter(assignee_id=assignee)
    if status:
        tasks = tasks.filter(status=status)

    context = {
        "tasks": tasks,
        "members": User.objects.filter(is_active=True).order_by("first_name"),
        "statuses": Task.Status.choices,
        "sel_assignee": assignee,
        "sel_status": status,
        "can_view_all": can_view_all,
    }
    if request.headers.get("HX-Request"):
        return render(request, "workboard/_task_table.html", context)
    return render(request, "workboard/task_list.html", context)


@login_required
def task_form(request, pk=None):
    instance = get_object_or_404(Task, pk=pk) if pk else None
    if instance and not _can_touch(request.user, instance):
        messages.error(request, "You can only edit tasks assigned to you.")
        return redirect("task_list")
    form = TaskForm(request.POST or None, instance=instance, user=request.user)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        if not task.pk:
            task.created_by = request.user
        task.save()
        return redirect("task_list")
    return render(request, "workboard/task_form.html", {"form": form, "instance": instance})


@login_required
def task_set_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST" and _can_touch(request.user, task):
        status = request.POST.get("status")
        if status in Task.Status.values:
            task.status = status
            task.save(update_fields=["status", "updated_at"])
    return render(request, "workboard/_task_row.html", {"task": task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        if _can_touch(request.user, task):
            task.delete()
        else:
            messages.error(request, "You can only delete tasks assigned to you.")
    return redirect("task_list")
