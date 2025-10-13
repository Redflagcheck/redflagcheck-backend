from django.contrib import admin
from .models import Analysis, Followup

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display  = ("analysis_id", "status", "created_at", "completed_at")
    ordering      = ("-created_at",)
    list_filter   = ("status", "created_at", "completed_at")
    search_fields = ("analysis_id", "email", "input_text")
    date_hierarchy = "created_at"


@admin.register(Followup)
class FollowupAdmin(admin.ModelAdmin):
    list_display = ("analysis", "position", "question_text", "answer_text")
    search_fields = ("question_text", "answer_text")
    list_filter = ("model_version",)