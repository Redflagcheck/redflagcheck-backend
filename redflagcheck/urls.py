from django.urls import path
from . import views

urlpatterns = [
    path('save_formdata/', views.form_submit, name='save_formdata'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('verify_token/', views.verify_token),
    path('check_verification_status/', views.check_verification_status, name='check_verification_status'),
    path('update_email/', views.update_email, name='update_email'),
    path('resend_magic_link/', views.resend_magic_link, name='resend_magic_link'),
    path('verify_magic_link/', views.verify_magic_link, name='verify_magic_link'),
    path('start_analysis/', views.start_analysis, name='start_analysis'),
    path('complete_analysis/', views.complete_analysis, name='complete_analysis'),
    path('confirm_analysis_viewed/', views.confirm_analysis_viewed, name='confirm_analysis_viewed'),

]
