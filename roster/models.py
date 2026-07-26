from django.contrib.auth.models import User
from django.db import models

# tailwind badge classes per colour key (static strings so the CDN JIT picks them up)
SHIFT_COLORS = {
    "sky": "bg-sky-100 text-sky-700 border-sky-200",
    "indigo": "bg-indigo-100 text-indigo-700 border-indigo-200",
    "violet": "bg-violet-100 text-violet-700 border-violet-200",
    "emerald": "bg-emerald-100 text-emerald-700 border-emerald-200",
    "amber": "bg-amber-100 text-amber-700 border-amber-200",
    "slate": "bg-slate-100 text-slate-600 border-slate-200",
}

DEFAULT_SHIFTS = [
    ("S1", "Morning", "06:00", "14:00", "sky"),
    ("S2", "Afternoon", "14:00", "22:00", "indigo"),
    ("S3", "Night", "22:00", "06:00", "violet"),
    ("G", "General", "09:00", "18:00", "emerald"),
    ("OC", "On-call", "00:00", "23:59", "amber"),
]


class Shift(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    color = models.CharField(max_length=10, choices=[(c, c) for c in SHIFT_COLORS], default="slate")
    is_active = models.BooleanField(default=True, help_text="Inactive shifts stay on old rosters but can't be newly assigned.")

    class Meta:
        ordering = ["start_time", "code"]

    def __str__(self):
        return f"{self.code} · {self.name}"

    @property
    def badge_classes(self):
        return SHIFT_COLORS.get(self.color, SHIFT_COLORS["slate"])

    @property
    def time_label(self):
        return f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"

    @property
    def assignment_count(self):
        return self.assignments.count()

    @classmethod
    def ensure_defaults(cls):
        if not cls.objects.exists():
            for code, name, start, end, color in DEFAULT_SHIFTS:
                cls.objects.create(code=code, name=name, start_time=start,
                                   end_time=end, color=color)


class ShiftAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shift_assignments")
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="assignments")

    class Meta:
        unique_together = [("user", "date")]
        ordering = ["date"]

    def __str__(self):
        return f"{self.user} {self.date} {self.shift.code}"
