import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id, text):
    """
    Envia uma mensagem para um chat específico no Telegram.
    Tenta primeiro com parse_mode='Markdown' e, se falhar com um Bad Request,
    tenta novamente sem formatação como fallback.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("A variável de ambiente TELEGRAM_BOT_TOKEN não está configurada.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Payload 1: Tentar com Markdown, que é mais tolerante a erros que o MarkdownV2.
    payload_markdown = {
        "chat_id": chat_id, "text": text, "parse_mode": "Markdown"
    }

    try:
        # Tentativa 1: Enviar com Markdown
        response = requests.post(url, json=payload_markdown)
        response.raise_for_status()
        logger.info(f"Mensagem enviada para o chat_id {chat_id} com sucesso (com Markdown).")

    except requests.exceptions.HTTPError as e:
        # Se o erro for um 400 Bad Request, é provável que seja um problema de formatação.
        if e.response.status_code == 400:
            error_details = e.response.json() if e.response.content else str(e)
            logger.warning(f"Falha ao enviar com Markdown (Bad Request): {error_details}. Tentando sem formatação.")
            # Payload 2: Fallback sem formatação
            payload_plain = {"chat_id": chat_id, "text": text}
            logger.info(f"Tentando enviar payload de fallback (texto plano): {payload_plain}")
            try:
                # Tentativa 2: Enviar como texto plano
                response_plain = requests.post(url, json=payload_plain)
                response_plain.raise_for_status()
                logger.info(f"Mensagem enviada para o chat_id {chat_id} com sucesso (fallback texto plano).")
            except requests.exceptions.RequestException as e_plain:
                error_details_plain = e_plain.response.json() if hasattr(e_plain, 'response') and e_plain.response.content else str(e_plain)
                logger.error(f"Erro ao enviar mensagem para o Telegram na tentativa de fallback: {error_details_plain}")
        else:
            # Se o erro for outro (e.g., 401, 403, 500), registre-o diretamente.
            logger.error(f"Erro HTTP inesperado ao enviar mensagem para o Telegram: {e}")
    except requests.exceptions.RequestException as e_conn:
        # Erro de conexão, timeout, etc.
        logger.error(f"Erro de conexão ao enviar mensagem para o Telegram: {e_conn}")