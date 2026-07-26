from django.contrib import admin

from .models import Shift, ShiftAssignment


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "start_time", "end_time", "color")


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "shift")
    list_filter = ("shift",)
