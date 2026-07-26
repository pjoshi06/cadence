from django.contrib import admin

from .models import BatchJob, JobRun


@admin.register(BatchJob)
class BatchJobAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "criticality", "schedule", "cluster", "is_active")
    list_filter = ("category", "criticality", "is_active")
    search_fields = ("name",)


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ("job", "run_date", "status", "remarks", "updated_by")
    list_filter = ("status",)
    date_hierarchy = "run_date"
