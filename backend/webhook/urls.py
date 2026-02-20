from django.urls import path
from .views import chatwoot_webhook

app_name = 'webhook'

urlpatterns = [
    path('', chatwoot_webhook, name='chatwoot_webhook'),
]