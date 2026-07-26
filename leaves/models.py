from django.contrib.auth.models import User
from django.db import models


class LeaveRequest(models.Model):
    class Type(models.TextChoices):
        ANNUAL = "ANNUAL", "Annual Leave"
        SICK = "SICK", "Sick Leave"
        CASUAL = "CASUAL", "Casual Leave"
        WFH = "WFH", "Work From Home"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.CharField(max_length=10, choices=Type.choices, default=Type.ANNUAL)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    approver = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_leaves"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} {self.leave_type} {self.start_date}"

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1
