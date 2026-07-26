from django.contrib import admin

from .models import BatchJob, ChangeEvent, ChangeRequest, JobRun


class ChangeEventInline(admin.TabularInline):
    model = ChangeEvent
    extra = 0


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("cr_number", "title", "status", "reviewer", "target_date")
    list_filter = ("status",)
    search_fields = ("cr_number", "title")
    inlines = [ChangeEventInline]


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
