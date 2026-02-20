from django.contrib import admin
from .models import Lead, PricingInfo, VendasAnalytics


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('get_status_badge', 'nome', 'email', 'telefone', 'curso_interesse', 'criado_em')
    list_filter = ('status', 'prioridade', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'curso_interesse')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Informações de Contato', {
            'fields': ('nome', 'email', 'telefone', 'whatsapp')
        }),
        ('Contexto de Venda', {
            'fields': ('curso_interesse', 'mensagem_original')
        }),
        ('Status e Acompanhamento', {
            'fields': ('status', 'prioridade', 'vendedor_responsavel', 'notas')
        }),
        ('Rastreamento', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_badge(self, obj):
        """Exibe status com emoji"""
        badges = {
            'novo': '🆕',
            'contato': '📞',
            'interessa': '👍',
            'negociacao': '💬',
            'convertido': '✅',
            'perdido': '❌',
        }
        emoji = badges.get(obj.status, '❓')
        return f"{emoji} {obj.get_status_display()}"
    
    get_status_badge.short_description = 'Status'


@admin.register(PricingInfo)
class PricingInfoAdmin(admin.ModelAdmin):
    list_display = ('curso_nome', 'valor_integral', 'valor_parcela', 'parcelas', 'desconto_display', 'ativo')
    list_filter = ('ativo', 'atualizado_em')
    search_fields = ('curso_nome',)
    readonly_fields = ('atualizado_em',)
    
    fieldsets = (
        ('Identificação', {
            'fields': ('curso_nome', 'ativo')
        }),
        ('Valores', {
            'fields': ('valor_integral', 'parcelas', 'valor_parcela', 'desconto_percentual')
        }),
        ('Descrição', {
            'fields': ('descricao',),
            'classes': ('collapse',)
        }),
        ('Rastreamento', {
            'fields': ('atualizado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def desconto_display(self, obj):
        if obj.desconto_percentual > 0:
            return f"🎁 {obj.desconto_percentual}% OFF"
        return "—"
    
    desconto_display.short_description = 'Desconto'


@admin.register(VendasAnalytics)
class VendasAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('data', 'total_leads', 'leads_contato', 'leads_convertidos', 'taxa_conversao_display')
    list_filter = ('data',)
    readonly_fields = ('data', 'total_leads', 'leads_novo', 'leads_contato', 'leads_convertidos', 'taxa_conversao')
    
    def taxa_conversao_display(self, obj):
        return f"{obj.taxa_conversao:.1f}%"
    
    taxa_conversao_display.short_description = 'Taxa de Conversão'
    
    def has_add_permission(self, request):
        """Não permite adicionar manualmente, apenas gerado automaticamente"""
        return False
