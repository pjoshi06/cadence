from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    tasks = Task.objects.select_related("assignee").all()
    assignee = request.GET.get("assignee", "")
    status = request.GET.get("status", "")
    if assignee == "me":
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
    }
    if request.headers.get("HX-Request"):
        return render(request, "workboard/_task_table.html", context)
    return render(request, "workboard/task_list.html", context)


@login_required
def task_form(request, pk=None):
    instance = get_object_or_404(Task, pk=pk) if pk else None
    form = TaskForm(request.POST or None, instance=instance)
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
    if request.method == "POST":
        status = request.POST.get("status")
        if status in Task.Status.values:
            task.status = status
            task.save(update_fields=["status", "updated_at"])
    return render(request, "workboard/_task_row.html", {"task": task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        task.delete()
    return redirect("task_list")
