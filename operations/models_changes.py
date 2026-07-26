from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class ChangeRequest(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        WT_SCHEDULED = "WT_SCHEDULED", "Walkthrough scheduled"
        WT_HELD = "WT_HELD", "Walkthrough held"
        REVIEW_1 = "REVIEW_1", "First review sent"
        REVIEW_2 = "REVIEW_2", "Second review sent"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    OPEN_STATUSES = ["RECEIVED", "WT_SCHEDULED", "WT_HELD", "REVIEW_1", "REVIEW_2"]

    cr_number = models.CharField("CR number", max_length=50, unique=True,
                                 help_text="e.g. CHG0034567")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    engineering_contact = models.CharField(max_length=100, blank=True)
    affected_system = models.CharField(max_length=100, blank=True)
    target_date = models.DateField("Implementation date", null=True, blank=True,
                                   help_text="Planned implementation / deployment date")
    runbook = models.FileField(upload_to="runbooks/", null=True, blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="assigned_changes")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.RECEIVED)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name="created_changes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.cr_number} — {self.title}"

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    def _event_at(self, kind):
        ev = self.events.filter(kind=kind).order_by("at").first()
        return ev.at if ev else None

    @property
    def runbook_received_at(self):
        return self._event_at(ChangeEvent.Kind.RUNBOOK_RECEIVED)

    @property
    def first_review_at(self):
        return self._event_at(ChangeEvent.Kind.REVIEW_1)

    @property
    def second_review_at(self):
        return self._event_at(ChangeEvent.Kind.REVIEW_2)

    @property
    def walkthrough_held_at(self):
        return self._event_at(ChangeEvent.Kind.WT_HELD)

    @property
    def walkthrough_scheduled_for(self):
        ev = self.events.filter(kind=ChangeEvent.Kind.WT_SCHEDULED).order_by("-at").first()
        return ev.scheduled_for if ev else None

    @property
    def decided_at(self):
        return (self._event_at(ChangeEvent.Kind.APPROVED)
                or self._event_at(ChangeEvent.Kind.REJECTED))

    @property
    def first_review_turnaround_days(self):
        start, end = self.runbook_received_at, self.first_review_at
        if start and end:
            return round((end - start).total_seconds() / 86400, 1)
        return None

    @property
    def total_cycle_days(self):
        end = self.decided_at
        if end:
            return round((end - self.created_at).total_seconds() / 86400, 1)
        return None

    @property
    def days_in_stage(self):
        last = self.events.exclude(kind=ChangeEvent.Kind.COMMENT).order_by("-at").first()
        anchor = last.at if last else self.created_at
        return (timezone.now() - anchor).days

    @property
    def age_days(self):
        return (timezone.now() - self.created_at).days


class ChangeEvent(models.Model):
    class Kind(models.TextChoices):
        CREATED = "CREATED", "Change registered"
        RUNBOOK_RECEIVED = "RUNBOOK_RECEIVED", "Runbook handed over"
        WT_SCHEDULED = "WT_SCHEDULED", "Walkthrough scheduled"
        WT_HELD = "WT_HELD", "Walkthrough held"
        REVIEW_1 = "REVIEW_1", "First review sent to engineering"
        REVIEW_2 = "REVIEW_2", "Second review sent to engineering"
        APPROVED = "APPROVED", "Change approved"
        REJECTED = "REJECTED", "Change rejected"
        COMMENT = "COMMENT", "Comment"

    # kind -> resulting CR status
    STATUS_MAP = {
        "RUNBOOK_RECEIVED": ChangeRequest.Status.RECEIVED,
        "WT_SCHEDULED": ChangeRequest.Status.WT_SCHEDULED,
        "WT_HELD": ChangeRequest.Status.WT_HELD,
        "REVIEW_1": ChangeRequest.Status.REVIEW_1,
        "REVIEW_2": ChangeRequest.Status.REVIEW_2,
        "APPROVED": ChangeRequest.Status.APPROVED,
        "REJECTED": ChangeRequest.Status.REJECTED,
    }

    change = models.ForeignKey(ChangeRequest, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    note = models.TextField(blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True,
                                         help_text="Walkthrough date/time")
    by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    at = models.DateTimeField(default=timezone.now,
                              help_text="When the milestone actually happened")
    recorded_at = models.DateTimeField(auto_now_add=True, null=True,
                                       help_text="When it was entered in the portal")

    class Meta:
        ordering = ["at"]

    def __str__(self):
        return f"{self.change.cr_number} {self.kind}"
