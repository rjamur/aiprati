"""
Bot AIpraTI - Atendimento conversacional com IA
Usa OpenRouter para respostas fluidas e naturais
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

SYSTEM_PROMPT = """Voce e a assistente virtual da AIpraTI, uma empresa especializada em chatbots inteligentes, automacao de atendimento com IA e qualificacao automatica de leads.

COMO VOCE DEVE SE COMPORTAR:
- Seja calorosa, acolhedora e atenciosa, como uma atendente humana de verdade.
- Responda de forma natural e fluida, como numa conversa real por WhatsApp.
- NUNCA use listas com bullet points ou asteriscos. Escreva em frases corridas.
- NUNCA use formatacao markdown (sem **, sem ##, sem *). Texto puro sempre.
- Use emojis com moderacao (1-2 por mensagem no maximo).
- Seja concisa. Respostas curtas e objetivas. Nao despeje informacoes.
- Faca UMA pergunta por vez. Espere a resposta antes de fazer outra.
- Varie suas respostas. NUNCA repita a mesma frase ou estrutura.

PRIMEIRA INTERACAO:
- Cumprimente de forma calorosa e natural. Diga que e da AIpraTI.
- Pergunte como a pessoa gostaria de ser chamada.
- Na mensagem seguinte (depois que souber o nome), pergunte os pronomes preferidos (ele/ela/elu).
- Nao pergunte nome e pronomes na mesma mensagem.

REGRAS RIGIDAS:
- A pessoa ja esta no WhatsApp. NUNCA pergunte o numero de WhatsApp dela.
- NUNCA ofereca para "entrar em contato" pedindo WhatsApp ou email logo de cara.
- Se a pessoa enviar um telefone ou email espontaneamente, agradeca.
- Se pedir um humano, diga que vai transferir.
- NUNCA liste servicos em formato de menu. Converse naturalmente.

SOBRE A AIPRATI (use essas infos naturalmente quando relevante, nao despeje tudo de uma vez):
- Criamos chatbots inteligentes para WhatsApp, Telegram e Web
- Usamos Chatwoot para atendimento, permitindo varios atendentes no mesmo numero
- Bot faz triagem e qualificacao de leads antes de passar para humano
- Integramos com CRMs como HubSpot, PipeDrive, RD Station
- Automacao com IA usando modelos como DeepSeek e GPT

PLANOS (so mencione se perguntarem sobre precos):
- Starter: a partir de R$ 199/mes, 1 canal, bot basico, ate 500 conversas/mes
- Business: a partir de R$ 399/mes, multicanal, IA avancada, ate 2000 conversas/mes
- Enterprise: sob consulta, ilimitado e personalizado

QUALIFICACAO (faca aos poucos, naturalmente, ao longo da conversa):
- Qual o segmento da empresa
- Quantos atendentes tem
- Quais canais usam
- Principal desafio de atendimento

DETECCAO DE NOME E PRONOMES:
- Quando a pessoa informar o nome, inclua na resposta: [NOME_DETECTADO: nome_aqui]
- Quando informar pronomes, inclua: [PRONOMES_DETECTADOS: pronomes_aqui]
- Esses marcadores sao invisíveis para o cliente. Inclua-os no final da resposta.

ESTILO DE ESCRITA:
- Escreva como se fosse uma mensagem de WhatsApp de uma pessoa real.
- Frases curtas. Pode quebrar em 2-3 linhas.
- Tom amigavel mas profissional.
- Exemplo bom: "Oi! Tudo bem? Sou a Bia da AIpraTI, prazer! Como posso te chamar? 😊"
- Exemplo ruim: "Olá! Sou o assistente da AIPRATI. Como posso ajudá-lo? Oferecemos: 1) Chatbots 2) Automação 3) CRM"
"""


def enviar_para_chatwoot(conversation_id, account_id, text):
    """Envia mensagem para o Chatwoot usando o token do Agent Bot"""
    try:
        url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        bot_token = os.environ.get("CHATWOOT_BOT_TOKEN_AIPRATI", os.environ.get("CHATWOOT_BOT_TOKEN", "LptzThPMMHWzMnqcERJvdwoL"))
        headers = {
            "api_access_token": bot_token,
            "Content-Type": "application/json"
        }
        payload = {
            "content": text,
            "message_type": "outgoing",
            "private": False
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"AIPRATI - Chatwoot response: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"AIPRATI - ERRO enviar Chatwoot: {e}")
        return None


def atualizar_contato_chatwoot(account_id, conversation_id, nome=None, pronomes=None):
    """Atualiza o contato no Chatwoot com nome e/ou custom attributes"""
    try:
        api_token = os.environ.get("CHATWOOT_API_TOKEN", "EvZGb4rPXHH3ccLEiNmoSDLq")
        conv_url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}"
        headers = {
            "api_access_token": api_token,
            "Content-Type": "application/json"
        }
        conv_response = requests.get(conv_url, headers=headers, timeout=10)
        conv_data = conv_response.json()
        
        contact_id = None
        if "meta" in conv_data and "sender" in conv_data["meta"]:
            contact_id = conv_data["meta"]["sender"].get("id")
        
        if not contact_id:
            print(f"AIPRATI - Nao encontrou contact_id para conversa {conversation_id}")
            return None
        
        contact_url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/contacts/{contact_id}"
        
        update_payload = {}
        if nome:
            update_payload["name"] = nome
        
        custom_attrs = {}
        if pronomes:
            custom_attrs["pronomes"] = pronomes
        if custom_attrs:
            update_payload["custom_attributes"] = custom_attrs
        
        if update_payload:
            response = requests.put(contact_url, headers=headers, json=update_payload, timeout=10)
            print(f"AIPRATI - Contato atualizado: {response.status_code}")
            return response.json()
        
        return None
    except Exception as e:
        print(f"AIPRATI - ERRO atualizar contato: {e}")
        return None


def processar_marcadores(resposta_ia, account_id, conversation_id):
    """Processa marcadores de nome e pronomes na resposta da IA"""
    nome_match = re.search(r"\[NOME_DETECTADO:\s*(.+?)\]", resposta_ia)
    if nome_match:
        nome = nome_match.group(1).strip()
        print(f"AIPRATI - Nome detectado: {nome}")
        atualizar_contato_chatwoot(account_id, conversation_id, nome=nome)
        resposta_ia = re.sub(r"\[NOME_DETECTADO:\s*.+?\]", "", resposta_ia).strip()
    
    pronomes_match = re.search(r"\[PRONOMES_DETECTADOS:\s*(.+?)\]", resposta_ia)
    if pronomes_match:
        pronomes = pronomes_match.group(1).strip()
        print(f"AIPRATI - Pronomes detectados: {pronomes}")
        atualizar_contato_chatwoot(account_id, conversation_id, pronomes=pronomes)
        resposta_ia = re.sub(r"\[PRONOMES_DETECTADOS:\s*.+?\]", "", resposta_ia).strip()
    
    return resposta_ia


def get_ai_response_aiprati(history_messages):
    """Chama OpenRouter com historico completo da conversa"""
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-chat")

        if not api_key:
            print("AIPRATI - OPENROUTER_API_KEY nao configurada!")
            return "Desculpe, estou com um problema tecnico momentaneo."

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history_messages:
            role = "assistant" if str(msg.sender) == "bot" else "user"
            content = str(msg.text) if msg.text else ""
            if content:
                messages.append({"role": role, "content": content})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://api.aiprati.com.br",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7
        }

        print(f"AIPRATI - Chamando OpenRouter com {len(messages)} mensagens...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            print(f"AIPRATI - Erro OpenRouter: {response.status_code} - {response.text[:200]}")
            return "Desculpe, tive um probleminha aqui. Pode repetir?"

        response_json = response.json()

        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"]
        else:
            print(f"AIPRATI - Resposta inesperada: {response_json}")
            return "Hmm, nao consegui processar. Pode repetir?"

    except Exception as e:
        print(f"AIPRATI - Erro critico OpenRouter: {e}")
        return "Tive um erro tecnico. Tente de novo em instantes."


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_aiprati(request):
    """Bot AIpraTI - Atendimento conversacional com IA"""
    try:
        data = json.loads(request.body)

        event = data.get("event")
        message_type = data.get("message_type")

        # Eventos que o Chatwoot Agent Bot envia e que devemos aceitar silenciosamente
        if event in ("conversation_created", "conversation_opened", "conversation_resolved",
                      "conversation_updated", "conversation_status_changed"):
            print(f"AIPRATI - Evento de conversa aceito: {event}")
            return JsonResponse({"status": "ok"}, status=200)

        if event == "message_updated":
            return JsonResponse({"status": "ok"}, status=200)

        if event != "message_created" or message_type != "incoming":
            return JsonResponse({"status": "ok"}, status=200)

        conversation = data.get("conversation", {}) or {}
        conversation_id = conversation.get("id")
        status = conversation.get("status")
        account_id = data.get("account", {}).get("id")
        content = (data.get("content") or "").strip()

        print(f"AIPRATI - INCOMING msg conv:{conversation_id} status:{status}")

        if not conversation_id or not account_id or not content:
            return JsonResponse({"status": "ok"}, status=200)

        if status not in ("open", "pending"):
            return JsonResponse({"status": "ok"}, status=200)

        content_lower = content.lower()

        # Transferir para humano se pedido
        if any(p in content_lower for p in ["humano", "atendente", "pessoa real", "falar com alguem"]):
            admin_id = os.environ.get("CHATWOOT_ADMIN_ID", "1")
            try:
                assign_url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}/assignments"
                headers = {
                    "api_access_token": os.environ.get("CHATWOOT_API_TOKEN", "EvZGb4rPXHH3ccLEiNmoSDLq"),
                    "Content-Type": "application/json"
                }
                requests.post(assign_url, headers=headers, json={"assignee_id": int(admin_id)}, timeout=10)
            except Exception as e:
                print(f"AIPRATI - Erro assign: {e}")
            enviar_para_chatwoot(conversation_id, account_id, "Claro! Vou te transferir para um dos nossos especialistas. Ele vai continuar o atendimento em instantes!")
            return JsonResponse({"status": "ok"}, status=200)

        # Salvar mensagem do usuario
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel="chatwoot",
            sender="user",
            text=content
        )

        # Buscar historico completo
        history = Message.objects.filter(
            channel="chatwoot",
            conversation_id=str(conversation_id)
        ).order_by("created_at")

        print(f"AIPRATI - Historico: {history.count()} msgs")

        # Gerar resposta com IA
        resposta = get_ai_response_aiprati(history)

        # Processar marcadores (nome, pronomes) e atualizar Chatwoot
        resposta = processar_marcadores(resposta, account_id, conversation_id)

        # Limpar qualquer formatacao markdown residual
        resposta = resposta.replace("**", "").replace("##", "").replace("# ", "")

        # Salvar resposta do bot
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel="chatwoot",
            sender="bot",
            text=resposta
        )

        # Enviar para Chatwoot
        print(f"AIPRATI - Resposta ({len(resposta)} chars)")
        enviar_para_chatwoot(conversation_id, account_id, resposta)

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print(f"AIPRATI - ERRO: {e}")
        import traceback
        traceback.print_exc()
        # IMPORTANTE: Sempre retornar 200 para o Chatwoot Agent Bot nao marcar como erro
        return JsonResponse({"status": "ok"}, status=200)
