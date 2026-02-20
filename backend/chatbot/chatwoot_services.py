import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatwootAPI:
    """
    Uma classe de cliente para interagir com a API do Chatwoot.
    """
    def __init__(self):
        self.base_url = settings.CHATWOOT_API_URL
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'api_access_token': settings.CHATWOOT_ACCESS_TOKEN,
        }

    def _request(self, method, endpoint, **kwargs):
        """
        Método auxiliar para fazer requisições à API do Chatwoot.
        """
        if not self.base_url or not settings.CHATWOOT_ACCESS_TOKEN:
            logger.error("Configurações da API do Chatwoot (URL ou Token) não definidas.")
            return None

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            # Retorna None para respostas 204 No Content
            return response.json() if response.status_code != 204 else None
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao chamar API do Chatwoot: {e.response.status_code} {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição ao chamar API do Chatwoot: {e}")
        return None

    def search_contact(self, query):
        """
        Busca por um contato usando um identificador (source_id).
        O 'query' deve ser o 'source_id' do contato no inbox específico.
        """
        logger.info(f"Buscando contato no Chatwoot com query: {query}")
        response = self._request('GET', f'contacts/search?q={query}')
        if response and response.get('payload'):
            # A API de busca pode retornar múltiplos contatos, vamos pegar o primeiro.
            return response['payload'][0]
        logger.info(f"Nenhum contato encontrado para a query: {query}")
        return None

    def create_contact(self, inbox_id, name, source_id):
        """
        Cria um novo contato associado a um inbox.
        'source_id' é o identificador único do usuário no canal (ex: chat_id do Telegram).
        """
        logger.info(f"Criando contato no Chatwoot para o inbox {inbox_id} com source_id: {source_id}")
        payload = {
            "inbox_id": inbox_id,
            "name": name,
            "source_id": source_id,
        }
        response = self._request('POST', 'contacts', json=payload)
        return response['payload'] if response and response.get('payload') else None

    def get_contact_conversations(self, contact_id):
        """
        Busca as conversas existentes para um contato.
        """
        logger.info(f"Buscando conversas para o contato_id: {contact_id}")
        return self._request('GET', f'contacts/{contact_id}/conversations')

    def create_conversation(self, contact_id, inbox_id, source_id):
        """
        Cria uma nova conversa para um contato em um inbox específico.
        """
        logger.info(f"Criando nova conversa para o contato {contact_id} no inbox {inbox_id}")
        payload = {
            "contact_id": contact_id,
            "inbox_id": inbox_id,
            "source_id": source_id,
        }
        return self._request('POST', 'conversations', json=payload)

    def create_message(self, conversation_id, content, message_type="outgoing"):
        """
        Cria uma nova mensagem em uma conversa.
        message_type pode ser 'incoming' ou 'outgoing'.
        """
        logger.info(f"Criando mensagem do tipo '{message_type}' na conversa {conversation_id}")
        payload = {
            "content": content,
            "message_type": message_type,
            "private": False, # Mensagens não são privadas por padrão
        }
        return self._request('POST', f'conversations/{conversation_id}/messages', json=payload)

    def get_or_create_contact(self, inbox_id, name, source_id):
        """
        Busca um contato pelo source_id. Se não encontrar, cria um novo.
        Retorna o dicionário do contato.
        """
        contact = self.search_contact(query=source_id)
        if contact:
            logger.info(f"Contato encontrado: ID {contact['id']}")
            return contact

        logger.info(f"Contato não encontrado, criando um novo.")
        return self.create_contact(inbox_id, name, source_id)

    def find_or_create_conversation(self, contact, inbox_id, source_id):
        """
        Busca uma conversa 'open' para o contato. Se não encontrar, cria uma nova.
        Retorna o dicionário da conversa.
        """
        contact_id = contact['id']
        conversations_data = self.get_contact_conversations(contact_id)

        if conversations_data:
            # Filtra por conversas que estão no mesmo inbox e não estão resolvidas
            for conv in conversations_data['payload']:
                if conv['inbox_id'] == inbox_id and conv['status'] != 'resolved':
                    logger.info(f"Conversa aberta encontrada: ID {conv['id']}")
                    return conv

        logger.info("Nenhuma conversa aberta encontrada, criando uma nova.")
        return self.create_conversation(contact_id, inbox_id, source_id)

    def toggle_conversation_status(self, conversation_id, status="open"):
        """
        Altera o status de uma conversa (ex: 'open', 'resolved', 'bot').
        """
        logger.info(f"Alterando status da conversa {conversation_id} para '{status}'")
        endpoint = f"conversations/{conversation_id}/toggle_status"
        payload = {"status": status}
        return self._request('POST', endpoint, json=payload)

    def assign_conversation(self, conversation_id, agent_id=None, team_id=None):
        """
        Atribui uma conversa a um agente ou a um time.
        Para desatribuir, passe agent_id=0.
        """
        if agent_id is None and team_id is None:
            logger.warning("Nenhum 'agent_id' ou 'team_id' fornecido para atribuição.")
            return None

        payload = {}
        if agent_id is not None:
            payload['assignee_id'] = agent_id
            logger.info(f"Atribuindo conversa {conversation_id} ao agente {agent_id}")
        if team_id is not None:
            payload['team_id'] = team_id
            logger.info(f"Atribuindo conversa {conversation_id} ao time {team_id}")

        endpoint = f"conversations/{conversation_id}/assignments"
        return self._request('POST', endpoint, json=payload)
