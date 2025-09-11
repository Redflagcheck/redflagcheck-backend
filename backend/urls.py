# backend/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from redflagcheck import views


urlpatterns = [
    path("admin/", admin.site.urls),

    # Health / root
    path("", lambda r: HttpResponse("OK"), name="root"),
    path("favicon.ico", lambda r: HttpResponse(status=204)),

    # MVP API endpoints
    path("api/intake", views.intake, name="api_intake"),
    path("api/feedback", views.feedback, name="api_feedback"),
    path("api/request_verification", views.request_verification, name="api_request_verification"),
    path("api/analysis/<uuid:analysis_id>/followup", views.analysis_followup, name="api_analysis_followup"),
    path("api/analysis/<uuid:analysis_id>/finalize", views.analysis_finalize, name="api_analysis_finalize"),
]

# media (alleen lokaal van nut)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



