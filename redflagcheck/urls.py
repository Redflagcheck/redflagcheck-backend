# backend/redflagcheck/urls.py

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # API endpoints
    path("api/intake", views.intake, name="api_intake"),
    path("api/feedback", views.feedback, name="api_feedback"),
    path("api/request_verification", views.request_verification, name="api_request_verification"),
]
