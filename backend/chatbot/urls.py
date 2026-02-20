from django.urls import path
from . import views
from . import unified_bot
from . import aiprati_bot

app_name = 'chatbot'

urlpatterns = [
    # Bot Unificado - Endpoint principal (faculdade)
    path('webhook/unified/', unified_bot.webhook_unified, name='unified_webhook'),

    # Bot AIpraTI - Endpoint para empresa de chatbots
    path('webhook/aiprati/', aiprati_bot.webhook_aiprati, name='aiprati_webhook'),

    # Webhook original (backup)
    path('webhook/chatwoot/', views.chatwoot_webhook, name='chatwoot_webhook'),
]
