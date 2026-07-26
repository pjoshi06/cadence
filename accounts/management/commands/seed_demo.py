"""Seeds demo data: team members, tasks, leaves and ~6 weeks of tickets."""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from leaves.models import LeaveRequest
from reports.models import Ticket
from roster.models import Shift, ShiftAssignment
from workboard.models import Task

MEMBERS = [
    ("puneet", "Puneet", "Joshi", "MANAGER", "Senior Manager - AMS", "AMS-Management", "Delivery, ServiceNow, SAP"),
    ("anita", "Anita", "Rao", "LEAD", "Team Lead - L2", "AMS-L2", "SAP ABAP, Batch Jobs"),
    ("rahul", "Rahul", "Mehta", "MEMBER", "Consultant - L1", "AMS-L1", "Access Mgmt, ITSM"),
    ("priya", "Priya", "Nair", "MEMBER", "Senior Consultant - L2", "AMS-L2", "Reporting, Oracle"),
    ("vikram", "Vikram", "Singh", "MEMBER", "Consultant - L2", "AMS-L2", "Java, Integrations"),
    ("sneha", "Sneha", "Kulkarni", "MEMBER", "Analyst - L1", "AMS-L1", "Monitoring, ITSM"),
]

CATEGORIES = ["Batch", "Access", "Reporting", "Integration", "Performance", "Data Fix", "Monitoring"]
SUMMARIES = [
    "Payment batch job failed in production",
    "User unable to login to vendor portal",
    "Invoice report showing wrong totals",
    "Interface to SAP stuck in queue",
    "Slow response on order entry screen",
    "Duplicate records in customer master",
    "Nightly backup job overran window",
    "Password reset for finance users",
    "Month-end report not generated",
    "IDoc failures in delivery interface",
    "Dashboard tiles not refreshing",
    "Purchase order approval workflow stuck",
]


class Command(BaseCommand):
    help = "Seed demo users, tasks, leaves and tickets"

    def handle(self, *args, **options):
        random.seed(42)
        users = {}
        for username, first, last, role, desig, group, skills in MEMBERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last,
                          "email": f"{username}@example.com"},
            )
            if created:
                user.set_password("demo1234")
                if role == "MANAGER":
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
            Profile.objects.get_or_create(
                user=user,
                defaults={"role": role, "designation": desig,
                          "assignment_group": group, "skills": skills,
                          "sn_user_id": f"{first.lower()}.{last.lower()}"},
            )
            users[username] = user
        self.stdout.write(f"Users: {len(users)} (password: demo1234)")

        if Ticket.objects.exists():
            self.stdout.write("Tickets already exist — skipping ticket seed.")
        else:
            now = timezone.now()
            names = [u.get_full_name() for k, u in users.items() if k != "puneet"]
            for i in range(120):
                opened = now - timedelta(days=random.randint(0, 42),
                                         hours=random.randint(0, 23))
                priority = random.choices(["P1", "P2", "P3", "P4"], weights=[6, 18, 50, 26])[0]
                resolved = None
                state = random.choices(["New", "In Progress", "On Hold"], weights=[3, 5, 2])[0]
                if random.random() < 0.78:
                    hours = {"P1": 6, "P2": 24, "P3": 72, "P4": 120}[priority]
                    resolved = opened + timedelta(hours=random.randint(1, hours * 2))
                    if resolved > now:
                        resolved = now - timedelta(hours=1)
                    state = random.choice(["Resolved", "Closed"])
                sla = None
                if resolved:
                    sla = random.random() < 0.93
                Ticket.objects.create(
                    number=f"INC{10000 + i:07d}",
                    short_description=random.choice(SUMMARIES),
                    category=random.choice(CATEGORIES),
                    priority=priority,
                    state=state,
                    opened_at=opened,
                    resolved_at=resolved,
                    assigned_to=random.choice(names),
                    assignment_group=random.choice(["AMS-L1", "AMS-L2"]),
                    sla_met=sla,
                )
            self.stdout.write("Tickets: 120 seeded")

        if not Task.objects.exists():
            today = timezone.localdate()
            task_specs = [
                ("Prepare RCA for payment batch failure", "anita", "P1", "IN_PROGRESS", "INC0010003", 1),
                ("KT session — new joiner onboarding", "priya", "P3", "TODO", "", 3),
                ("Monthly SLA review deck", "puneet", "P2", "IN_PROGRESS", "", 2),
                ("Fix duplicate customer master records", "vikram", "P2", "BLOCKED", "INC0010021", 4),
                ("Update runbook for nightly jobs", "sneha", "P4", "TODO", "", 7),
                ("Access recertification batch 2", "rahul", "P3", "IN_PROGRESS", "", 5),
                ("Patch validation — July window", "vikram", "P2", "TODO", "", 6),
                ("Client governance call minutes", "puneet", "P3", "DONE", "", 0),
                ("Interface monitoring automation POC", "anita", "P3", "IN_PROGRESS", "", 10),
                ("Close ageing P4 tickets review", "sneha", "P3", "TODO", "", 2),
            ]
            for title, who, prio, status, ref, due in task_specs:
                Task.objects.create(
                    title=title, assignee=users[who], priority=prio, status=status,
                    ticket_ref=ref, source="SERVICENOW" if ref else "MANUAL",
                    due_date=today + timedelta(days=due) if due else None,
                    created_by=users["puneet"],
                )
            self.stdout.write("Tasks: 10 seeded")

        if not LeaveRequest.objects.exists():
            today = timezone.localdate()
            LeaveRequest.objects.create(
                user=users["priya"], leave_type="ANNUAL",
                start_date=today, end_date=today + timedelta(days=1),
                reason="Family function", status="APPROVED",
                approver=users["puneet"], decided_at=timezone.now(),
            )
            LeaveRequest.objects.create(
                user=users["vikram"], leave_type="SICK",
                start_date=today + timedelta(days=4), end_date=today + timedelta(days=5),
                reason="Medical appointment", status="PENDING",
            )
            LeaveRequest.objects.create(
                user=users["sneha"], leave_type="ANNUAL",
                start_date=today + timedelta(days=9), end_date=today + timedelta(days=13),
                reason="Vacation", status="PENDING",
            )
            self.stdout.write("Leaves: 3 seeded")

        if not ShiftAssignment.objects.exists():
            Shift.ensure_defaults()
            shifts = {s.code: s for s in Shift.objects.all()}
            today = timezone.localdate()
            monday = today - timedelta(days=today.weekday())
            pattern = {
                "anita": ["G", "G", "G", "G", "G", None, None],
                "rahul": ["S1", "S1", "S1", "S1", "S1", "OC", None],
                "priya": ["S2", "S2", "S2", "S2", "S2", None, None],
                "vikram": ["S3", "S3", "S3", "S3", "S3", None, "OC"],
                "sneha": ["S1", "S1", "S2", "S2", "S1", None, None],
                "puneet": ["G", "G", "G", "G", "G", None, None],
            }
            count = 0
            for week_offset in (0, 1):
                for username, codes in pattern.items():
                    for i, code in enumerate(codes):
                        if code:
                            ShiftAssignment.objects.create(
                                user=users[username],
                                date=monday + timedelta(days=i, weeks=week_offset),
                                shift=shifts[code],
                            )
                            count += 1
            self.stdout.write(f"Roster: {count} shift assignments seeded (this week + next)")

        self.stdout.write(self.style.SUCCESS("Demo data ready. Login: puneet / demo1234"))
