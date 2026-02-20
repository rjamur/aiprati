import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from chatbot.models import Message
from chatbot import services as chatbot_services
from chatbot.chatwoot_services import ChatwootAPI

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook_handler(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            logger.info("Webhook do Telegram recebido.")

            message_data = payload.get('message')
            if not message_data:
                logger.warning("Webhook ignorado: payload não contém a chave 'message'.")
                return JsonResponse({"status": "ok_no_message"})

            chat_id = str(message_data.get('chat', {}).get('id'))
            text = message_data.get('text')
            user_name = message_data.get('from', {}).get('first_name', 'Usuário do Telegram')

            if not chat_id or not text:
                logger.info("Webhook ignorado: sem chat_id ou texto.")
                return JsonResponse({"status": "ok_no_chat_id_or_text"})

            logger.info(f"Mensagem recebida do chat_id {chat_id}: '{text}'")

            # --- Integração com Chatwoot ---
            chatwoot_api = ChatwootAPI()
            inbox_id = settings.TELEGRAM_INBOX_ID
            if not inbox_id:
                logger.error("TELEGRAM_INBOX_ID não está configurado.")
                # Continua sem a integração para não parar o bot
            else:
                # 1. Garante que o contato e a conversa existam no Chatwoot
                contact = chatwoot_api.get_or_create_contact(inbox_id, user_name, chat_id)
                if contact:
                    conversation = chatwoot_api.find_or_create_conversation(contact, inbox_id, chat_id)
                    if conversation:
                        # 2. Registra a mensagem do usuário no Chatwoot
                        chatwoot_api.create_message(
                            conversation['id'], text, message_type='incoming'
                        )
                    else:
                        logger.error(f"Não foi possível criar ou encontrar conversa para o contato {contact['id']}")
                else:
                    logger.error(f"Não foi possível criar ou encontrar contato com source_id {chat_id}")


            # --- Lógica do Bot (existente) ---
            Message.objects.create(
                conversation_id=chat_id, channel='telegram', sender='user', text=text
            )
            conversation_history = Message.objects.filter(
                channel='telegram', conversation_id=chat_id
            ).order_by('created_at')
            bot_response_text = chatbot_services.get_ai_response(conversation_history)

            if not bot_response_text or not bot_response_text.strip():
                logger.warning("A resposta da IA está vazia. Nenhuma mensagem será enviada.")
                return JsonResponse({"status": "ok_empty_ai_response"})

            Message.objects.create(
                conversation_id=chat_id, channel='telegram', sender='bot', text=bot_response_text
            )
            chatbot_services.send_message_to_channel(
                channel='telegram', conversation_id=chat_id, text=bot_response_text
            )

            # --- Registrar resposta do bot no Chatwoot ---
            if 'conversation' in locals() and conversation:
                chatwoot_api.create_message(
                    conversation['id'], bot_response_text, message_type='outgoing'
                )

            return JsonResponse({"status": "ok"})
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON do Telegram.")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Erro inesperado no webhook do Telegram: {e}", exc_info=True)
            return JsonResponse({"error": "Internal Server Error"}, status=500)

    return JsonResponse({"error": "Method Not Allowed"}, status=405)
