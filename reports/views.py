import calendar
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .csv_import import import_tickets
from .forms import GenerateReportForm, TemplateUploadForm, TicketCSVForm
from .models import GeneratedReport, ReportTemplate, Ticket
from .pptgen import build_report

SAMPLE_CSV = """number,short_description,priority,state,opened_at,resolved_at,assigned_to,assignment_group,category,sla_met
INC0012345,Payment batch job failed in production,P1,Resolved,2026-07-20 08:15,2026-07-20 11:40,Anita Rao,AMS-L2,Batch,yes
INC0012346,User unable to login to vendor portal,P3,In Progress,2026-07-21 10:05,,Rahul Mehta,AMS-L1,Access,
INC0012347,Invoice report showing wrong totals,P2,New,2026-07-22 14:30,,Priya Nair,AMS-L2,Reporting,
"""


def _period_for(report_type, ref):
    if report_type == "DSR":
        return ref, ref
    if report_type == "WSR":
        start = ref - timedelta(days=ref.weekday())
        return start, start + timedelta(days=6)
    last = calendar.monthrange(ref.year, ref.month)[1]
    return ref.replace(day=1), ref.replace(day=last)


@login_required
def report_home(request):
    gen_form = GenerateReportForm(request.POST or None)
    if request.method == "POST" and gen_form.is_valid():
        data = gen_form.cleaned_data
        start, end = _period_for(data["report_type"], data["reference_date"])
        template = data["template"]
        buf = build_report(
            data["report_type"], start, end,
            template_path=template.file.path if template else None,
            highlights=data["highlights"],
        )
        report = GeneratedReport(
            report_type=data["report_type"],
            period_start=start,
            period_end=end,
            template=template,
            highlights=data["highlights"],
            created_by=request.user,
        )
        filename = f"{data['report_type']}_{start.isoformat()}_{end.isoformat()}.pptx"
        report.file.save(filename, ContentFile(buf.read()))
        report.save()
        messages.success(request, f"{report.get_report_type_display()} generated.")
        return redirect("report_home")

    return render(request, "reports/report_home.html", {
        "gen_form": gen_form,
        "history": GeneratedReport.objects.select_related("template", "created_by")[:20],
        "ticket_count": Ticket.objects.count(),
    })


@login_required
def template_list(request):
    form = TemplateUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        tpl = form.save(commit=False)
        tpl.uploaded_by = request.user
        tpl.save()
        messages.success(request, f'Template "{tpl.name}" uploaded.')
        return redirect("template_list")
    return render(request, "reports/template_list.html", {
        "form": form,
        "templates": ReportTemplate.objects.select_related("uploaded_by"),
    })


@login_required
def template_delete(request, pk):
    if request.method == "POST":
        tpl = get_object_or_404(ReportTemplate, pk=pk)
        tpl.file.delete(save=False)
        tpl.delete()
        messages.success(request, "Template deleted.")
    return redirect("template_list")


@login_required
def ticket_list(request):
    form = TicketCSVForm()
    if request.method == "POST":
        form = TicketCSVForm(request.POST, request.FILES)
        if form.is_valid():
            created, updated, errors = import_tickets(form.cleaned_data["file"])
            messages.success(request, f"Import complete: {created} created, {updated} updated.")
            for err in errors[:5]:
                messages.warning(request, err)
            return redirect("ticket_list")

    tickets = Ticket.objects.all()
    state = request.GET.get("state", "")
    if state == "open":
        tickets = tickets.exclude(state__in=Ticket.OPEN_EXCLUDED_STATES)
    elif state == "closed":
        tickets = tickets.filter(state__in=Ticket.OPEN_EXCLUDED_STATES)
    return render(request, "reports/ticket_list.html", {
        "form": form,
        "tickets": tickets[:200],
        "total": tickets.count(),
        "sel_state": state,
    })


@login_required
def sample_csv(request):
    response = HttpResponse(SAMPLE_CSV, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ticket_import_sample.csv"'
    return response
