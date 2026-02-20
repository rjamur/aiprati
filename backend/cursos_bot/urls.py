from django.urls import path
from . import views

app_name = 'cursos_bot'

urlpatterns = [
    path('webhook/', views.webhook_cursos, name='webhook_cursos'),
    path('listar/', views.listar_cursos, name='listar_cursos'),
]
