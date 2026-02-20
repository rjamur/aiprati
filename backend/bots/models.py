"""
Modelo para gerenciar múltiplos Agent Bots
"""
from django.db import models
from django.core.validators import URLValidator


class AgentBot(models.Model):
    """
    Armazena configurações de múltiplos bots integrados com Chatwoot
    """
    BOT_TYPES = [
        ('cursos', 'Bot de Cursos'),
        ('vendas', 'Bot de Vendas'),
        ('suporte', 'Bot de Suporte'),
        ('leads', 'Bot de Leads'),
        ('custom', 'Bot Customizado'),
    ]
    
    # Identificação
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome único do bot (ex: cursos_bot, vendas_bot)"
    )
    bot_type = models.CharField(
        max_length=20,
        choices=BOT_TYPES,
        default='custom'
    )
    description = models.TextField(
        blank=True,
        help_text="Descrição do bot e seu propósito"
    )
    
    # Segurança
    bot_token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Token único para validar requisições (gerado pelo Chatwoot)"
    )
    
    # Configuração
    webhook_url = models.CharField(
        max_length=500,
        validators=[URLValidator()],
        help_text="URL do webhook (ex: https://api.aiprati.com.br/api/v1/cursos/webhook/)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Se desativado, não processará mensagens"
    )
    
    # Rastreamento
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_request = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp da última requisição"
    )
    request_count = models.BigIntegerField(
        default=0,
        help_text="Total de requisições processadas"
    )
    
    class Meta:
        verbose_name = "Agent Bot"
        verbose_name_plural = "Agent Bots"
        ordering = ['-is_active', 'name']
        indexes = [
            models.Index(fields=['bot_token']),
            models.Index(fields=['is_active', 'name']),
        ]
    
    def __str__(self):
        status = "🟢" if self.is_active else "🔴"
        return f"{status} {self.name} ({self.get_bot_type_display()})"
    
    def validate_token(self, token):
        """Valida se o token fornecido corresponde ao deste bot"""
        return self.is_active and self.bot_token == token
    
    def record_request(self):
        """Registra uma nova requisição"""
        from django.utils import timezone
        self.request_count += 1
        self.last_request = timezone.now()
        self.save(update_fields=['request_count', 'last_request'])
