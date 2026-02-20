from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/', include('chatbot.urls')),
    path('api/v1/telegram/', include('telegram_bridge.urls')),
    path('api/v1/twilio/', include('twilio_bridge.urls')),
    path('api/v1/cursos/', include('cursos_bot.urls')),
    path('api/v1/vendas/', include('vendas_bot.urls')),
]
