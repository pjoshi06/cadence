from django import forms

from accounts.forms import StyledModelForm

from .models import Task


class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assignee", "priority", "status", "ticket_ref", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
