from django.contrib import admin
from .models import Analysis

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("analysis_id", "email_from_data", "created_at", "completed_at")
    readonly_fields = ("created_at", "completed_at")
    search_fields = ("analysis_id", "data__email")
    list_filter = ("created_at",)

    # ⬇️ voeg deze regel toe
    exclude = ("followup_answers",)

    def email_from_data(self, obj):
        return (obj.data or {}).get("email", "")
    email_from_data.short_description = "Email"