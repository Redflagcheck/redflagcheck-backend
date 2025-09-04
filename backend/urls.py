from django.contrib import admin
from django.urls import path, include
from redflagcheck import views
from django.conf import settings
from django.conf.urls.static import static
from redflagcheck.views import form_submit  # import view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/verify_token/', views.verify_token),  # ← forceer directe toegang
    path('api/', include('redflagcheck.urls')),
    path('api/save_formdata/', form_submit, name='save_formdata'),  # <-- exact pad van je frontend
    path('save_formdata/', form_submit, name='save_formdata'),  # <-- exact pad van je frontend

]



urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


