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

    path("api/analyze", views.analyze, name="api_analyze"),
    path("api/result/<uuid:analysis_id>", views.result, name="api_result"),
    path("api/audit_event", views.audit_event, name="api_audit_event"),
]

# media (alleen lokaal van nut)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



