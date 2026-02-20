import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifica a conexão com a API do Chatwoot usando as configurações do projeto.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando verificação de conexão com o Chatwoot...")

        # 1. Verificar se as configurações essenciais existem
        if not all([settings.CHATWOOT_API_URL, settings.CHATWOOT_ACCESS_TOKEN]):
            raise CommandError(
                "As configurações CHATWOOT_API_URL e/ou CHATWOOT_ACCESS_TOKEN não foram encontradas. "
                "Verifique seu arquivo .env.local e as configurações em core/settings.py."
            )

        # 2. Montar os headers da requisição
        headers = {
            'Content-Type': 'application/json',
            'api_access_token': settings.CHATWOOT_ACCESS_TOKEN,
        }

        # 3. Escolher um endpoint simples para testar (listar conversas é uma boa opção)
        # Usamos o CHATWOOT_API_URL que já contém a conta
        test_endpoint = f"{settings.CHATWOOT_API_URL}/conversations"

        self.stdout.write(f"Tentando acessar o endpoint: {test_endpoint}")

        # 4. Fazer a requisição
        try:
            response = requests.get(test_endpoint, headers=headers, timeout=10)
            response.raise_for_status()  # Lança uma exceção para status de erro (4xx ou 5xx)

            # 5. Analisar a resposta
            self.stdout.write(self.style.SUCCESS(
                f"Conexão bem-sucedida! Status: {response.status_code}. "
                f"O bot consegue se comunicar com o Chatwoot."
            ))

        except requests.exceptions.HTTPError as e:
            error_message = f"Erro HTTP: {e.response.status_code} - {e.response.reason}\n"
            try:
                error_details = e.response.json()
                error_message += f"Detalhes: {error_details.get('message', 'Nenhuma mensagem de erro específica.')}"
            except requests.exceptions.JSONDecodeError:
                error_message += f"Resposta não contém JSON válido: {e.response.text[:200]}..."
            
            if e.response.status_code == 401:
                error_message += "\n\nCausa provável: O CHATWOOT_ACCESS_TOKEN está incorreto ou não tem permissão."
            
            raise CommandError(error_message)

        except requests.exceptions.RequestException as e:
            raise CommandError(f"Ocorreu um erro inesperado na requisição: {e}")