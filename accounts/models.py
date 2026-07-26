from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        LEAD = "LEAD", "Team Lead"
        MEMBER = "MEMBER", "Team Member"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    designation = models.CharField(max_length=100, blank=True)
    sn_user_id = models.CharField("ServiceNow user ID", max_length=100, blank=True)
    assignment_group = models.CharField(max_length=100, blank=True)
    skills = models.CharField(max_length=255, blank=True, help_text="Comma separated, e.g. SAP, Java, Oracle")
    phone = models.CharField(max_length=20, blank=True)
    annual_leave_balance = models.DecimalField(max_digits=5, decimal_places=1, default=24)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_approver(self):
        return self.role in (self.Role.ADMIN, self.Role.MANAGER, self.Role.LEAD)

    @property
    def skill_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    @property
    def initials(self):
        name = self.user.get_full_name() or self.user.username
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:2].upper()
