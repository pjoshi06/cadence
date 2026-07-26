from django import forms
from django.contrib.auth.models import User

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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        is_approver = user and hasattr(user, "profile") and user.profile.is_approver
        if is_approver:
            self.fields["assignee"].queryset = (
                User.objects.filter(is_active=True).order_by("first_name")
            )
        elif user:
            # members can only create/keep tasks for themselves
            self.fields["assignee"].queryset = User.objects.filter(pk=user.pk)
            self.fields["assignee"].initial = user.pk
            self.fields["assignee"].disabled = True
