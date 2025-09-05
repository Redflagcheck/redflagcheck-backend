# backend/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from redflagcheck import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # MVP API endpoints
    path("api/intake", views.intake, name="api_intake"),
    path("api/feedback", views.feedback, name="api_feedback"),
    path("api/request_verification", views.request_verification, name="api_request_verification"),
]

# media (alleen nodig als je lokaal uploads serveert)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

