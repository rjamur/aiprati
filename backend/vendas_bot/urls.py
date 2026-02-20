from django.urls import path
from . import views

app_name = 'vendas_bot'

urlpatterns = [
    path('webhook/', views.webhook_vendas, name='webhook_vendas'),
    path('leads/', views.listar_leads, name='listar_leads'),
]
