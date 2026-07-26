from django.contrib import admin

from .models import GeneratedReport, ReportTemplate, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("number", "short_description", "priority", "state", "opened_at")
    list_filter = ("priority", "state")
    search_fields = ("number", "short_description")


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "client_name", "is_client_approved", "uploaded_at")


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("report_type", "period_start", "period_end", "created_by", "created_at")
    list_filter = ("report_type",)
