from django.urls import path
from . import views

urlpatterns = [
    path('save_formdata/', views.form_submit, name='save_formdata'),
]