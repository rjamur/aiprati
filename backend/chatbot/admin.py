from django.contrib import admin

from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'channel', 'conversation_id', 'sender', 'text')
    list_filter = ('channel', 'sender',)
    search_fields = ('text', 'conversation_id')
