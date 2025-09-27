from django.contrib import admin
from .models import Analysis, Followup, AuditEvent

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("analysis_id", "email", "status", "created_at", "completed_at")
    readonly_fields = ("created_at", "updated_at", "completed_at")
    search_fields = ("analysis_id", "email", "input_text")
    list_filter = ("status", "created_at", "completed_at")
    ordering = ("-created_at",)
