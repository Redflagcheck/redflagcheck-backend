# redflagcheck/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('save_formdata', views.form_submit, name='save_formdata'),  # ✅ correcte koppeling
    # eventueel later:
    # path('email_status', views.email_status, name='email_status')
]