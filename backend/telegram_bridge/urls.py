from django.urls import path
from . import views

app_name = 'telegram_bridge'

urlpatterns = [
    path('webhook/', views.telegram_webhook_handler, name='webhook'),
]