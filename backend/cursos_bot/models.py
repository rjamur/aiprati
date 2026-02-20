from django.db import models


class Curso(models.Model):
    TIPO_CHOICES = [
        ('bacharelado', 'Bacharelado'),
        ('licenciatura', 'Licenciatura'),
        ('tecnologico', 'Tecnólogo'),
    ]

    nome = models.CharField(max_length=255, unique=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    duracao = models.CharField(max_length=50)  # Ex: "4 anos", "2 anos"
    descricao = models.TextField(blank=True, null=True)
    link_matricula = models.URLField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tipo', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.tipo})"
