import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_twilio_whatsapp_message(recipient_id, text):
    """
    Envia uma mensagem de WhatsApp para um destinatário específico usando a API do Twilio.
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number_raw = settings.TWILIO_WHATSAPP_NUMBER

    if not all([account_sid, auth_token, from_number_raw]):
        logger.error("As variáveis de ambiente do Twilio não estão configuradas corretamente.")
        return

    # Garante que o número 'from' tenha o prefixo 'whatsapp:' exigido pela API.
    # O 'recipient_id' (que vem do webhook como 'From') já vem no formato correto.
    if not from_number_raw.startswith('whatsapp:'):
        from_number_formatted = f"whatsapp:{from_number_raw}"
    else:
        from_number_formatted = from_number_raw

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(from_=from_number_formatted, body=text, to=recipient_id)
        logger.info(f"Mensagem enviada para {recipient_id} via Twilio. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem para o Twilio: {e}")