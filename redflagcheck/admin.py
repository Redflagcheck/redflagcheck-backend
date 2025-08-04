from django.contrib import admin
from .models import Analysis, User

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    # ... eventueel extra instellingen ...
    pass

    class Meta:
        verbose_name_plural = "Analyses"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
