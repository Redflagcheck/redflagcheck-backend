from django.urls import path
from . import views

urlpatterns = [
    path('save_formdata/', views.form_submit, name='save_formdata'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('verify_token/', views.verify_token),
    path('request_magic_link/', views.request_magic_link),
    path('resend_magic_link/', views.resend_magic_link),

]