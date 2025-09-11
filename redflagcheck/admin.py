from django.contrib import admin
from .models import Analysis

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("analysis_id", "email_from_data", "created_at", "completed_at")
    readonly_fields = ("created_at", "completed_at", "show_followup_questions_full")
    search_fields = ("analysis_id", "data__email")
    list_filter = ("created_at",)


    def email_from_data(self, obj):
        return (obj.data or {}).get("email", "")
    email_from_data.short_description = "Email"


    def show_followup_questions_full(self, obj):
        return (obj.data or {}).get("followup_questions_full", "")
    show_followup_questions_full.short_description = "Follow-up Q+WHY"