from django.contrib import admin
from .models import Curso


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'duracao', 'atualizado_em')
    list_filter = ('tipo', 'atualizado_em')
    search_fields = ('nome', 'descricao')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo', 'duracao')
        }),
        ('Detalhes', {
            'fields': ('descricao', 'link_matricula')
        }),
        ('Rastreamento', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
