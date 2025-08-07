from django.contrib import admin
from django.urls import path, include
from redflagcheck import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/verify_token/', views.verify_token),  # ← forceer directe toegang
    path('api/', include('redflagcheck.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)