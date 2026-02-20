from django.contrib import admin
from .models import AgentBot


@admin.register(AgentBot)
class AgentBotAdmin(admin.ModelAdmin):
    list_display = ('get_status', 'name', 'bot_type', 'request_count', 'last_request')
    list_filter = ('is_active', 'bot_type', 'created_at')
    search_fields = ('name', 'bot_token', 'description')
    readonly_fields = ('bot_token', 'request_count', 'last_request', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'bot_type', 'description', 'is_active')
        }),
        ('Segurança', {
            'fields': ('bot_token',),
            'description': 'Token usado para validar requisições do webhook'
        }),
        ('Configuração', {
            'fields': ('webhook_url',)
        }),
        ('Estatísticas', {
            'fields': ('request_count', 'last_request', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status(self, obj):
        """Exibe status visual do bot"""
        return '🟢 Ativo' if obj.is_active else '🔴 Inativo'
    
    get_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Gera token automático se não existir"""
        if not change:  # Se é novo bot
            import secrets
            obj.bot_token = secrets.token_urlsafe(32)
        super().save_model(request, obj, form, change)
