"""Seeds demo data: team members, tasks, leaves and ~6 weeks of tickets."""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from leaves.models import LeaveRequest
from operations.models import BatchJob, ChangeEvent, ChangeRequest, JobRun
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

        if not BatchJob.objects.exists():
            jobs_spec = [
                ("INFRA_BACKUP_PROD", "INFRA", "HIGH", "Daily 01:00", "PRD-CLUS-01"),
                ("INFRA_LOG_ARCHIVE", "INFRA", "LOW", "Daily 03:30", "PRD-CLUS-01"),
                ("INFRA_DISK_CLEANUP", "INFRA", "MEDIUM", "Daily 04:00", "PRD-CLUS-02"),
                ("INFRA_HEALTHCHECK_AM", "INFRA", "MEDIUM", "Daily 06:00", "PRD-CLUS-01"),
                ("DWH_NIGHTLY_LOAD", "PIPELINE", "HIGH", "Daily 02:00", "DWH-CLUS"),
                ("DWH_DIM_REFRESH", "PIPELINE", "MEDIUM", "Daily 02:45", "DWH-CLUS"),
                ("FIN_INTERFACE_SAP", "PIPELINE", "HIGH", "Daily 23:30", "PRD-CLUS-01"),
                ("CRM_DELTA_SYNC", "PIPELINE", "MEDIUM", "Hourly 06-22", "PRD-CLUS-02"),
                ("MDM_CUSTOMER_MERGE", "PIPELINE", "MEDIUM", "Daily 05:00", "MDM-CLUS"),
                ("RPT_SALES_EXTRACT", "PIPELINE", "LOW", "Daily 05:30", "DWH-CLUS"),
                ("RPT_REGULATORY_FEED", "PIPELINE", "HIGH", "Mon-Fri 06:30", "DWH-CLUS"),
                ("ARCHIVE_PURGE_MONTHLY", "PIPELINE", "LOW", "1st of month 02:00", "PRD-CLUS-02"),
            ]
            for name, cat, crit, sched, cluster in jobs_spec:
                BatchJob.objects.create(name=name, category=cat, criticality=crit,
                                        schedule=sched, cluster=cluster)
            today = timezone.localdate()
            fail_plan = {  # (job_name, days_ago): remarks
                ("FIN_INTERFACE_SAP", 0): "Connection timeout to SAP PI - INC0010121",
                ("DWH_NIGHTLY_LOAD", 2): "Source file arrived late - rerun OK next day",
                ("INFRA_LOG_ARCHIVE", 4): "Mount point full - cleaned & rerun",
                ("RPT_REGULATORY_FEED", 1): "Upstream data quality check failed",
            }
            runs = 0
            for job in BatchJob.objects.all():
                for days_ago in range(6, -1, -1):
                    d = today - timedelta(days=days_ago)
                    if "Mon-Fri" in job.schedule and d.weekday() >= 5:
                        continue
                    if "month" in job.schedule and d.day != 1:
                        continue
                    remarks = fail_plan.get((job.name, days_ago))
                    if remarks:
                        status = "FAILED"
                    elif days_ago == 0 and job.name in ("CRM_DELTA_SYNC", "INFRA_HEALTHCHECK_AM"):
                        status = "RUNNING"
                        remarks = ""
                    else:
                        status = "SUCCESS"
                        remarks = ""
                    JobRun.objects.create(job=job, run_date=d, status=status,
                                          remarks=remarks or "")
                    runs += 1
            self.stdout.write(f"Batch jobs: {BatchJob.objects.count()} jobs, {runs} runs seeded")

        if not ChangeRequest.objects.exists():
            now = timezone.now()

            def ev(cr, kind, days_ago, by, note="", sched=None):
                ChangeEvent.objects.create(
                    change=cr, kind=kind, by=by, note=note,
                    scheduled_for=sched, at=now - timedelta(days=days_ago),
                )

            cr1 = ChangeRequest.objects.create(
                cr_number="CHG0034551", title="Upgrade payment gateway adapter to v4.2",
                affected_system="Payments", engineering_contact="Arjun Patel",
                target_date=timezone.localdate() + timedelta(days=5),
                reviewer=users["anita"], status="REVIEW_1", created_by=users["puneet"],
            )
            ev(cr1, "CREATED", 6, users["puneet"])
            ev(cr1, "RUNBOOK_RECEIVED", 6, users["puneet"])
            ev(cr1, "WT_SCHEDULED", 5, users["anita"], sched=now - timedelta(days=3))
            ev(cr1, "WT_HELD", 3, users["anita"], "Rollback section needs more detail.")
            ev(cr1, "REVIEW_1", 2, users["anita"],
               "Sent review: add explicit rollback timings and DB backup step before deploy.")

            cr2 = ChangeRequest.objects.create(
                cr_number="CHG0034562", title="Archive job re-partitioning on DWH cluster",
                affected_system="DWH", engineering_contact="Meera Iyer",
                target_date=timezone.localdate() + timedelta(days=12),
                reviewer=users["vikram"], status="WT_SCHEDULED", created_by=users["puneet"],
            )
            ev(cr2, "CREATED", 2, users["puneet"])
            ev(cr2, "RUNBOOK_RECEIVED", 1, users["vikram"])
            ev(cr2, "WT_SCHEDULED", 1, users["vikram"], sched=now + timedelta(days=2))

            cr3 = ChangeRequest.objects.create(
                cr_number="CHG0034538", title="TLS config hardening on vendor portal",
                affected_system="Vendor Portal", engineering_contact="Arjun Patel",
                target_date=timezone.localdate() - timedelta(days=2),
                reviewer=users["anita"], status="APPROVED", created_by=users["puneet"],
            )
            ev(cr3, "CREATED", 10, users["puneet"])
            ev(cr3, "RUNBOOK_RECEIVED", 10, users["puneet"])
            ev(cr3, "WT_SCHEDULED", 9, users["anita"], sched=now - timedelta(days=8))
            ev(cr3, "WT_HELD", 8, users["anita"])
            ev(cr3, "REVIEW_1", 7, users["anita"], "Minor comments on cipher list.")
            ev(cr3, "APPROVED", 4, users["puneet"], "Approved for implementation window Sat 02:00.")

            self.stdout.write("Changes: 3 seeded with event timelines")

        self.stdout.write(self.style.SUCCESS("Demo data ready. Login: puneet / demo1234"))
