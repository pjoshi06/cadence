from django.contrib.auth.models import User
from django.db import models


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        BLOCKED = "BLOCKED", "Blocked"
        DONE = "DONE", "Done"

    class Priority(models.TextChoices):
        P1 = "P1", "P1 - Critical"
        P2 = "P2", "P2 - High"
        P3 = "P3", "P3 - Moderate"
        P4 = "P4", "P4 - Low"

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        SERVICENOW = "SERVICENOW", "ServiceNow"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=2, choices=Priority.choices, default=Priority.P3)
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.MANUAL)
    ticket_ref = models.CharField(max_length=50, blank=True, help_text="e.g. INC0012345")
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
