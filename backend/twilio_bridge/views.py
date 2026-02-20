import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from chatbot.models import Message
from chatbot import services as chatbot_services
from chatbot.chatwoot_services import ChatwootAPI

logger = logging.getLogger(__name__)

@csrf_exempt
def twilio_webhook_handler(request):
    if request.method == 'POST':
        try:
            # 1. Extrair dados do webhook do Twilio (vem como form data)
            source_id = request.POST.get('From') # Ex: 'whatsapp:+5511999998888'
            text = request.POST.get('Body')
            user_name = request.POST.get('ProfileName', 'Usuário do WhatsApp')

            if not source_id or not text:
                logger.warning("Webhook do Twilio ignorado: 'From' ou 'Body' ausentes.")
                return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', content_type='text/xml')

            logger.info(f"Mensagem recebida de {source_id} via Twilio: '{text}'")

            # --- Integração com Chatwoot ---
            chatwoot_api = ChatwootAPI()
            inbox_id = settings.TWILIO_INBOX_ID
            if not inbox_id:
                logger.error("TWILIO_INBOX_ID não está configurado.")
            else:
                contact = chatwoot_api.get_or_create_contact(inbox_id, user_name, source_id)
                if contact:
                    conversation = chatwoot_api.find_or_create_conversation(contact, inbox_id, source_id)
                    if conversation:
                        chatwoot_api.create_message(
                            conversation['id'], text, message_type='incoming'
                        )
                    else:
                        logger.error(f"Não foi possível criar ou encontrar conversa para o contato {contact['id']}")
                else:
                    logger.error(f"Não foi possível criar ou encontrar contato com source_id {source_id}")


            # --- Lógica do Bot (existente) ---
            Message.objects.create(
                conversation_id=source_id, channel='twilio_whatsapp', sender='user', text=text
            )
            conversation_history = Message.objects.filter(
                channel='twilio_whatsapp', conversation_id=source_id
            ).order_by('created_at')
            bot_response_text = chatbot_services.get_ai_response(conversation_history)

            if not bot_response_text or not bot_response_text.strip():
                logger.warning("A resposta da IA está vazia. Nenhuma mensagem será enviada.")
                return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', content_type='text/xml')

            Message.objects.create(
                conversation_id=source_id, channel='twilio_whatsapp', sender='bot', text=bot_response_text
            )
            chatbot_services.send_message_to_channel(
                channel='twilio_whatsapp', conversation_id=source_id, text=bot_response_text
            )

            # --- Registrar resposta do bot no Chatwoot ---
            if 'conversation' in locals() and conversation:
                chatwoot_api.create_message(
                    conversation['id'], bot_response_text, message_type='outgoing'
                )

        except Exception as e:
            logger.error(f"Erro ao processar webhook do Twilio: {e}", exc_info=True)
            # Retornar um erro 500 não impede o Twilio de tentar novamente, mas é melhor que travar.
            return HttpResponse(status=500)

        # Twilio espera uma resposta TwiML vazia para não enviar uma resposta automática de erro.
        return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', content_type='text/xml')

    return HttpResponse("Error: Method Not Allowed", status=405)
