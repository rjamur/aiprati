"""
Models para o bot de vendas e captura de leads
"""
from django.db import models
from django.utils import timezone


class Lead(models.Model):
    """
    Modelo para armazenar leads capturados pelo bot de vendas
    """
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('contato', 'Contato Realizado'),
        ('interessa', 'Interessado'),
        ('negociacao', 'Em Negociação'),
        ('convertido', 'Convertido'),
        ('perdido', 'Lead Perdido'),
    ]
    
    # Informações do lead
    nome = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    
    # Contexto
    curso_interesse = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Qual curso o lead está interessado"
    )
    mensagem_original = models.TextField(
        blank=True,
        help_text="Primeira mensagem/dúvida do lead"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='novo'
    )
    prioridade = models.IntegerField(
        default=0,
        help_text="0=baixa, 1=média, 2=alta"
    )
    
    # Rastreamento
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    vendedor_responsavel = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Email do vendedor responsável"
    )
    notas = models.TextField(
        blank=True,
        help_text="Notas internas sobre o lead"
    )
    
    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['status', '-criado_em']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


class PricingInfo(models.Model):
    """
    Informações de preço e formas de pagamento
    """
    MODALIDADE_CHOICES = [
        ('integral', 'Integral'),
        ('parcelado', 'Parcelado'),
        ('promocao', 'Promoção'),
    ]
    
    curso_nome = models.CharField(
        max_length=255,
        help_text="Nome do curso (ex: Administração, Engenharia)"
    )
    valor_integral = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor para pagamento à vista"
    )
    parcelas = models.IntegerField(
        default=12,
        help_text="Número de parcelas disponíveis"
    )
    valor_parcela = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor de cada parcela"
    )
    desconto_percentual = models.IntegerField(
        default=0,
        help_text="Percentual de desconto (se houver)"
    )
    descricao = models.TextField(
        blank=True,
        help_text="Descrição da oferta"
    )
    
    ativo = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Informação de Preço"
        verbose_name_plural = "Informações de Preço"
        unique_together = ('curso_nome',)
        ordering = ['curso_nome']
    
    def __str__(self):
        return f"{self.curso_nome} - R$ {self.valor_integral}"
    
    def valor_com_desconto(self):
        """Calcula valor com desconto aplicado"""
        if self.desconto_percentual > 0:
            from decimal import Decimal
            fator = Decimal(1) - (Decimal(self.desconto_percentual) / Decimal(100))
            return (self.valor_integral * fator).quantize(Decimal('0.01'))
        return self.valor_integral


class VendasAnalytics(models.Model):
    """
    Analytics de conversão e desempenho do bot de vendas
    """
    data = models.DateField(auto_now_add=True)
    total_leads = models.IntegerField(default=0)
    leads_novo = models.IntegerField(default=0)
    leads_contato = models.IntegerField(default=0)
    leads_convertidos = models.IntegerField(default=0)
    taxa_conversao = models.FloatField(default=0.0)  # em %
    
    class Meta:
        verbose_name = "Analytic de Vendas"
        verbose_name_plural = "Analytics de Vendas"
        ordering = ['-data']
        unique_together = ('data',)
    
    def __str__(self):
        return f"{self.data} - {self.leads_convertidos}/{self.total_leads} conversões"
