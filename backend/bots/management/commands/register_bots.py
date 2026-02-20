"""
Management command para registrar Agent Bots iniciais
"""
from django.core.management.base import BaseCommand
from bots.models import AgentBot
import secrets


class Command(BaseCommand):
    help = 'Registra Agent Bots iniciais no banco de dados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--bot',
            type=str,
            help='Registrar um bot específico (cursos, vendas, suporte)'
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Token customizado (se não fornecido, será gerado automaticamente)'
        )
    
    def handle(self, *args, **options):
        bot_name = options.get('bot')
        custom_token = options.get('token')
        
        bots_config = {
            'cursos': {
                'bot_type': 'cursos',
                'description': 'Bot para responder dúvidas sobre cursos e graduação',
                'webhook_url': 'https://api.aiprati.com.br/api/v1/cursos/webhook/',
            },
            'vendas': {
                'bot_type': 'vendas',
                'description': 'Bot para responder dúvidas de vendas e matrículas',
                'webhook_url': 'https://api.aiprati.com.br/api/v1/vendas/webhook/',
            },
            'suporte': {
                'bot_type': 'suporte',
                'description': 'Bot para atendimento e suporte ao cliente',
                'webhook_url': 'https://api.aiprati.com.br/api/v1/suporte/webhook/',
            },
        }
        
        if bot_name and bot_name not in bots_config:
            self.stdout.write(
                self.style.ERROR(f'Bot "{bot_name}" não encontrado. Opções: {", ".join(bots_config.keys())}')
            )
            return
        
        # Registrar um ou todos os bots
        bots_para_registrar = {bot_name: bots_config[bot_name]} if bot_name else bots_config
        
        for name, config in bots_para_registrar.items():
            # Verificar se já existe
            if AgentBot.objects.filter(name=name).exists():
                self.stdout.write(
                    self.style.WARNING(f'Bot "{name}" já existe. Pulando...')
                )
                continue
            
            # Gerar token
            token = custom_token if custom_token else secrets.token_urlsafe(32)
            
            # Criar bot
            bot = AgentBot.objects.create(
                name=name,
                bot_type=config['bot_type'],
                description=config['description'],
                webhook_url=config['webhook_url'],
                bot_token=token,
                is_active=True,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Bot "{name}" registrado com sucesso!')
            )
            self.stdout.write(f'   Token: {token}')
            self.stdout.write(f'   Webhook: {config["webhook_url"]}')
            self.stdout.write('')
