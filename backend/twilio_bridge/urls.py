from django.urls import path
from . import views

app_name = 'twilio_bridge'

urlpatterns = [
    path('webhook/', views.twilio_webhook_handler, name='webhook'),
]