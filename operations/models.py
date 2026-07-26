from django.contrib.auth.models import User
from django.db import models

from .models_changes import ChangeEvent, ChangeRequest  # noqa: F401


class BatchJob(models.Model):
    class Category(models.TextChoices):
        INFRA = "INFRA", "Infrastructure"
        PIPELINE = "PIPELINE", "Data Pipeline"
        OTHER = "OTHER", "Other"

    class Criticality(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    name = models.CharField(max_length=120, unique=True, help_text="Control-M job name")
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.PIPELINE)
    criticality = models.CharField(max_length=6, choices=Criticality.choices, default=Criticality.MEDIUM)
    schedule = models.CharField(max_length=100, blank=True, help_text='e.g. "Daily 02:00" or "Mon-Fri 23:30"')
    cluster = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class JobRun(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        RUNNING = "RUNNING", "Running"
        SKIPPED = "SKIPPED", "Skipped"

    job = models.ForeignKey(BatchJob, on_delete=models.CASCADE, related_name="runs")
    run_date = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices)
    remarks = models.CharField(max_length=255, blank=True, help_text="e.g. failure reason / INC number")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("job", "run_date")]
        ordering = ["-run_date"]

    def __str__(self):
        return f"{self.job.name} {self.run_date} {self.status}"
