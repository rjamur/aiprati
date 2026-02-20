"""
Bot AIpraTI - Atendimento para empresa de chatbots, automacao e qualificacao de leads
Versao com debug detalhado
"""
import json
import logging
import re
import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Message

logger = logging.getLogger(__name__)


def enviar_para_chatwoot(conversation_id, account_id, text):
    """Envia mensagem para o Chatwoot usando o token do Agent Bot"""
    try:
        url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        bot_token = os.environ.get("CHATWOOT_BOT_TOKEN_AIPRATI", os.environ.get("CHATWOOT_BOT_TOKEN", "LptzThPMMHWzMnqcERJvdwoL"))
        
        logger.info(f"[AIPRATI] Enviando para Chatwoot - conv_id: {conversation_id}, account_id: {account_id}, token: {bot_token[:10]}...")
        
        headers = {
            "api_access_token": bot_token,
            "Content-Type": "application/json"
        }
        payload = {
            "content": text,
            "message_type": "outgoing",
            "private": False
        }
        
        logger.info(f"[AIPRATI] URL: {url}")
        logger.info(f"[AIPRATI] Payload: {payload}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        logger.info(f"[AIPRATI] Chatwoot response status: {response.status_code}, body: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"[AIPRATI] ERRO ao enviar para Chatwoot: {e}")
        logger.error(f"[AIPRATI] Detalhes - conv_id: {conversation_id}, account_id: {account_id}")
        return None


def assign_to_admin(conversation_id, account_id, admin_id):
    """Atribui conversa para admin"""
    try:
        url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}/assignments"
        headers = {
            "api_access_token": os.environ.get("CHATWOOT_API_TOKEN", "EvZGb4rPXHH3ccLEiNmoSDLq"),
            "Content-Type": "application/json"
        }
        payload = {"assignee_id": admin_id}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"[AIPRATI] Erro ao assignar para admin: {e}")
        return None


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_aiprati(request):
    """
    Bot AIpraTI - Atendimento para empresa de chatbots, automacao e qualificacao de leads
    """
    try:
        data = json.loads(request.body)
        
        logger.info(f"[AIPRATI] ===== WEBHOOK CHAMADO =====")
        logger.info(f"[AIPRATI] Payload completo: {json.dumps(data, indent=2)}")

        event = data.get("event")
        message_type = data.get("message_type")
        conversation = data.get("conversation", {}) or {}
        conversation_id = conversation.get("id")
        status = conversation.get("status")
        account_id = data.get("account", {}).get("id")
        content = (data.get("content") or "").strip()
        
        logger.info(f"[AIPRATI] event: {event}, message_type: {message_type}, conv_id: {conversation_id}, account_id: {account_id}, status: {status}")

        # So processar mensagens incoming
        if event != "message_created" or message_type != "incoming":
            logger.info(f"[AIPRATI] Ignorado: not_incoming")
            return JsonResponse({"status": "ignored", "reason": "not_incoming"})

        # Verificar dados basicos
        if not conversation_id or not account_id or not content:
            logger.warning(f"[AIPRATI] Ignorado: missing_data - conv_id: {conversation_id}, account_id: {account_id}, content: {content}")
            return JsonResponse({"status": "ignored", "reason": "missing_data"})

        # So responder se status open/pending
        if status not in ("open", "pending"):
            logger.info(f"[AIPRATI] Ignorado: status {status}")
            return JsonResponse({"status": "ignored", "reason": f"status_{status}"})

        content_lower = content.lower()

        # Transferir para humano se pedido explicitamente
        if any(palavra in content_lower for palavra in ["humano", "atendente", "pessoa"]):
            admin_id = os.environ.get("CHATWOOT_ADMIN_ID", "1")
            assign_to_admin(conversation_id, account_id, admin_id)
            enviar_para_chatwoot(conversation_id, account_id, "Transferindo para um de nossos especialistas...")
            return JsonResponse({"status": "success", "action": "handoff"})

        # Salvar mensagem
        logger.info(f"[AIPRATI] Salvando mensagem do usuario...")
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel="chatwoot",
            sender="user",
            text=content
        )

        # Gerar resposta baseada no conteudo
        logger.info(f"[AIPRATI] Gerando resposta...")
        resposta = gerar_resposta_aiprati(content, conversation_id)
        logger.info(f"[AIPRATI] Resposta gerada: {resposta[:100]}...")

        # Salvar resposta
        logger.info(f"[AIPRATI] Salvando resposta do bot...")
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel="chatwoot",
            sender="bot",
            text=resposta
        )

        # Enviar para Chatwoot
        logger.info(f"[AIPRATI] Enviando resposta para Chatwoot...")
        result = enviar_para_chatwoot(conversation_id, account_id, resposta)
        
        if result:
            logger.info(f"[AIPRATI] Resposta enviada com sucesso!")
        else:
            logger.error(f"[AIPRATI] Falha ao enviar resposta para Chatwoot!")

        return JsonResponse({"status": "success", "bot": "aiprati"})

    except Exception as e:
        logger.error(f"[AIPRATI] ERRO CRITICO no bot: {e}")
        import traceback
        logger.error(f"[AIPRATI] Traceback: {traceback.format_exc()}")
        return JsonResponse({"status": "error", "reason": str(e)}, status=500)


def gerar_resposta_aiprati(content, conversation_id):
    """Gera resposta baseada no conteudo da mensagem - Persona AIpraTI"""
    content_lower = content.lower()

    # Detectar numeros de WhatsApp/telefone
    phone_patterns = [
        r"\b(\d{10,11})\b",
        r"\((\d{2})\)\s*(\d{4,5})-?(\d{4})",
        r"(\d{2})\s*(\d{4,5})-?(\d{4})",
    ]
    phone_found = False
    for pattern in phone_patterns:
        if re.search(pattern, content):
            phone_found = True
            break

    # Detectar emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    email_found = re.search(email_pattern, content)

    # Se forneceu WhatsApp ou email
    if phone_found or email_found:
        contact_type = "WhatsApp" if phone_found else "email"
        contact_value = content.strip()
        return f"""Perfeito! Recebi seu {contact_type}: {contact_value}

Proximos passos:
1. Nossa equipe vai entrar em contato em ate 2 horas
2. Vamos entender sua necessidade em detalhes
3. Preparar uma proposta personalizada de chatbot/automacao

Enquanto isso, posso te ajudar com mais alguma duvida?
- Nossos servicos de chatbot
- Integracoes disponiveis
- Cases de sucesso

Obrigado por escolher a AIpraTI!"""

    # Saudacoes
    elif any(palavra in content_lower for palavra in ["oi", "ola", "bom dia", "boa tarde", "boa noite", "hello", "hi"]):
        return """Ola! Sou o assistente virtual da AIpraTI!

Somos especialistas em:
- Chatbots inteligentes (WhatsApp, Telegram, Web)
- Automacao de atendimento com IA
- Qualificacao automatica de leads
- Integracao com Chatwoot para equipes

Como posso ajudar voce hoje?"""

    # Resposta generica
    else:
        return f"""Vi que voce quer saber sobre: "{content}"

A AIpraTI oferece:
- Chatbots inteligentes para WhatsApp, Telegram e Web
- Automacao de atendimento com IA
- Qualificacao automatica de leads
- Chatwoot para equipes (varios atendentes, 1 numero)

Me diga o que procura ou me passe seu WhatsApp que nossa equipe liga pra voce!"""
