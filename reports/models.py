from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    OPEN_EXCLUDED_STATES = ["Resolved", "Closed", "Cancelled"]

    number = models.CharField(max_length=50, unique=True)
    short_description = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=2, default="P3")  # P1..P4
    state = models.CharField(max_length=50, default="New")
    opened_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.CharField(max_length=100, blank=True)
    assignment_group = models.CharField(max_length=100, blank=True)
    sla_met = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return self.number

    @property
    def is_open(self):
        return self.state not in self.OPEN_EXCLUDED_STATES

    @property
    def age_days(self):
        end = self.resolved_at or timezone.now()
        return (end - self.opened_at).days


class ReportTemplate(models.Model):
    name = models.CharField(max_length=100)
    client_name = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to="templates/")
    is_client_approved = models.BooleanField(
        default=True, verbose_name="Client-approved template"
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    class Kind(models.TextChoices):
        DSR = "DSR", "Daily Status Report"
        WSR = "WSR", "Weekly Status Report"
        MSR = "MSR", "Monthly Status Report"

    report_type = models.CharField(max_length=3, choices=Kind.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Blank = built-in default template",
    )
    file = models.FileField(upload_to="reports/")
    highlights = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_type} {self.period_start}"

    @property
    def period_label(self):
        if self.report_type == self.Kind.DSR or self.period_start == self.period_end:
            return self.period_start.strftime("%d %b %Y")
        return f"{self.period_start.strftime('%d %b')} – {self.period_end.strftime('%d %b %Y')}"
