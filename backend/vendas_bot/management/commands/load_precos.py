"""
Management command para seed de informações de preço
"""
from django.core.management.base import BaseCommand
from vendas_bot.models import PricingInfo
from decimal import Decimal


class Command(BaseCommand):
    help = 'Carrega informações de preço dos cursos'
    
    def handle(self, *args, **options):
        # Limpar preços existentes
        PricingInfo.objects.all().delete()
        
        # Lista de cursos com preços (exemplos)
        precos = [
            {
                'curso_nome': 'Administração',
                'valor_integral': Decimal('3500.00'),
                'parcelas': 12,
                'valor_parcela': Decimal('350.00'),
                'desconto_percentual': 10,
                'descricao': 'Curso de Administração EAD com 10% de desconto para matrícula imediata'
            },
            {
                'curso_nome': 'Engenharia Civil',
                'valor_integral': Decimal('4500.00'),
                'parcelas': 20,
                'valor_parcela': Decimal('225.00'),
                'desconto_percentual': 0,
                'descricao': 'Curso de Engenharia Civil com financiamento em até 20x'
            },
            {
                'curso_nome': 'Pedagogia',
                'valor_integral': Decimal('2800.00'),
                'parcelas': 12,
                'valor_parcela': Decimal('280.00'),
                'desconto_percentual': 15,
                'descricao': 'Licenciatura em Pedagogia com 15% de black friday'
            },
            {
                'curso_nome': 'Análise e Desenvolvimento de Sistemas',
                'valor_integral': Decimal('3200.00'),
                'parcelas': 12,
                'valor_parcela': Decimal('320.00'),
                'desconto_percentual': 5,
                'descricao': 'Tecnólogo com taxa de empregabilidade de 95%'
            },
            {
                'curso_nome': 'Psicologia',
                'valor_integral': Decimal('4000.00'),
                'parcelas': 18,
                'valor_parcela': Decimal('222.00'),
                'desconto_percentual': 0,
                'descricao': 'Curso presencial + EAD (modalidade mista)'
            },
        ]
        
        created = 0
        for preco_data in precos:
            preco, created_flag = PricingInfo.objects.get_or_create(
                curso_nome=preco_data['curso_nome'],
                defaults=preco_data
            )
            if created_flag:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Preço criado: {preco.curso_nome}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {created} preços carregados com sucesso!')
        )
