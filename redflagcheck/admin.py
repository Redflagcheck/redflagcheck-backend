from django.contrib import admin
from .models import User, Analysis

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'balance', 'email_verified', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('email',)
    list_filter = ('email_verified',)
    fieldsets = (
        (None, {
            'fields': ('email', 'name', 'password_hash', 'token', 'balance', 'email_verified')
        }),
        ('Magic Link', {
            'fields': ('magic_code', 'magic_code_expiry')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('analysis_id', 'user_email', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('user_email', 'message', 'ocr')
    list_filter = ('created_at',)

