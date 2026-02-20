"""
Bot AIpraTI - Atendimento para empresa de chatbots, automacao e qualificacao de leads
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
        logger.info(f"Chatwoot response status: {response.status_code}, body: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao enviar para Chatwoot (AIpraTI): {e}")
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
        logger.error(f"Erro ao assignar para admin (AIpraTI): {e}")
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

        event = data.get("event")
        message_type = data.get("message_type")
        conversation = data.get("conversation", {}) or {}
        conversation_id = conversation.get("id")
        status = conversation.get("status")
        account_id = data.get("account", {}).get("id")
        content = (data.get("content") or "").strip()

        # So processar mensagens incoming
        if event != "message_created" or message_type != "incoming":
            return JsonResponse({"status": "ignored", "reason": "not_incoming"})

        # Verificar dados basicos
        if not conversation_id or not account_id or not content:
            return JsonResponse({"status": "ignored", "reason": "missing_data"})

        # So responder se status open/pending
        if status not in ("open", "pending"):
            return JsonResponse({"status": "ignored", "reason": f"status_{status}"})

        content_lower = content.lower()

        # Transferir para humano se pedido explicitamente
        if any(palavra in content_lower for palavra in ["humano", "atendente", "pessoa"]):
            admin_id = os.environ.get("CHATWOOT_ADMIN_ID", "1")
            assign_to_admin(conversation_id, account_id, admin_id)
            enviar_para_chatwoot(conversation_id, account_id, "Transferindo para um de nossos especialistas...")
            return JsonResponse({"status": "success", "action": "handoff"})

        # Salvar mensagem
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel="chatwoot",
            sender="user",
            text=content
        )

        # Gerar resposta baseada no conteudo
        resposta = gerar_resposta_aiprati(content, conversation_id)

        # Salvar resposta
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel="chatwoot",
            sender="bot",
            text=resposta
        )

        # Enviar para Chatwoot
        enviar_para_chatwoot(conversation_id, account_id, resposta)

        return JsonResponse({"status": "success", "bot": "aiprati"})

    except Exception as e:
        logger.error(f"Erro no bot AIpraTI: {e}")
        return JsonResponse({"status": "error", "reason": str(e)}, status=500)


def gerar_resposta_aiprati(content, conversation_id):
    """
    Gera resposta baseada no conteudo da mensagem - Persona AIpraTI
    """
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

    # Perguntas sobre chatbot/automacao
    elif any(palavra in content_lower for palavra in ["chatbot", "chat bot", "bot", "automacao", "automatizar", "automatico"]):
        return """Nossos Chatbots Inteligentes

A AIpraTI desenvolve chatbots sob medida para sua empresa:

WhatsApp Business:
- Atendimento 24/7 automatizado
- Qualificacao de leads antes do atendente
- Respostas inteligentes com IA
- Menu interativo e fluxos personalizados

Telegram:
- Bots para grupos e canais
- Automacao de processos internos
- Notificacoes e alertas automaticos

Web Chat:
- Widget para seu site
- Captura de leads automatica
- Integracao com seu CRM

Todos integrados ao Chatwoot para gestao unificada!

Quer saber mais sobre algum canal especifico? Ou me passe seu WhatsApp para uma demonstracao!"""

    # Perguntas sobre Chatwoot
    elif any(palavra in content_lower for palavra in ["chatwoot", "atendimento", "equipe", "time", "agentes"]):
        return """Solucao Chatwoot para Equipes

O Chatwoot e a plataforma que usamos para centralizar atendimentos:

Vantagens:
- Varios atendentes no mesmo numero de WhatsApp
- Distribuicao automatica de conversas
- Bot de triagem antes do atendente humano
- Historico completo de conversas
- Dashboard com metricas de atendimento
- Integracao com WhatsApp, Telegram, Email, Web

Como funciona:
1. Cliente manda mensagem no WhatsApp
2. Bot AIpraTI faz a triagem e qualificacao
3. Conversa e direcionada ao atendente certo
4. Tudo registrado e organizado

Quer uma demonstracao? Me passe seu WhatsApp!"""

    # Perguntas sobre IA / inteligencia artificial
    elif any(palavra in content_lower for palavra in ["ia", "inteligencia artificial", "gpt", "openai", "deepseek", "modelo"]):
        return """IA Aplicada ao Atendimento

Usamos modelos de IA de ponta para turbinar seus chatbots:

O que nossa IA faz:
- Entende linguagem natural (nao precisa de menu rigido)
- Responde perguntas frequentes automaticamente
- Qualifica leads com perguntas inteligentes
- Aprende com o historico de conversas
- Transfere para humano quando necessario

Tecnologias que usamos:
- OpenRouter (acesso a varios modelos de IA)
- DeepSeek, GPT e outros modelos avancados
- Integracao com bases de conhecimento da sua empresa

O resultado: menos trabalho manual, mais vendas, clientes mais satisfeitos!

Quer saber como aplicar na sua empresa? Me passe seu WhatsApp!"""

    # Perguntas sobre preco/valor
    elif any(palavra in content_lower for palavra in ["preco", "valor", "custo", "quanto", "custa", "plano", "planos", "mensalidade"]):
        return """Planos e Valores AIpraTI

Nossos planos de chatbot e automacao:

Plano Starter - a partir de R$ 199/mes:
- 1 canal (WhatsApp ou Telegram)
- Bot de atendimento basico
- Ate 500 conversas/mes
- Suporte por email

Plano Business - a partir de R$ 399/mes:
- Multicanal (WhatsApp + Telegram + Web)
- Bot com IA avancada
- Ate 2.000 conversas/mes
- Chatwoot para ate 5 atendentes
- Suporte prioritario

Plano Enterprise - sob consulta:
- Canais ilimitados
- IA personalizada para seu negocio
- Conversas ilimitadas
- Atendentes ilimitados
- Integracoes customizadas
- Gerente de conta dedicado

Quer um orcamento personalizado? Me passe seu WhatsApp ou email!"""

    # Perguntas sobre lead/qualificacao/vendas
    elif any(palavra in content_lower for palavra in ["lead", "leads", "qualificacao", "vendas", "vender", "prospectar", "prospeccao", "funil"]):
        return """Qualificacao Automatica de Leads

Nossos chatbots ajudam sua equipe a vender mais:

Como funciona:
1. Lead chega pelo WhatsApp/site
2. Bot faz perguntas de qualificacao automaticas
3. Identifica nivel de interesse e necessidade
4. Classifica o lead (quente, morno, frio)
5. Direciona para o vendedor certo via Chatwoot

Integracoes com CRM:
- HubSpot
- PipeDrive
- RD Station
- Bitrix24
- Ou seu CRM atual

Resultados dos nossos clientes:
- 3x mais leads qualificados
- 50% menos tempo de resposta
- 40% mais conversao em vendas

Quer ver uma demonstracao? Me diga seu segmento ou desafio!"""

    # Perguntas sobre integracao
    elif any(palavra in content_lower for palavra in ["integracao", "integrar", "api", "crm", "erp", "sistema"]):
        return """Integracoes Disponiveis

A AIpraTI integra seus chatbots com:

Canais de comunicacao:
- WhatsApp Business API
- Telegram Bot API
- Facebook Messenger
- Instagram Direct
- Web Chat (widget para site)
- Email

CRM e Vendas:
- HubSpot
- PipeDrive
- RD Station
- Bitrix24

Plataformas:
- Chatwoot (central de atendimento)
- N8N (automacao de fluxos)
- Zapier
- Make (Integromat)

Desenvolvimento custom:
- APIs REST personalizadas
- Webhooks
- Banco de dados proprio

Precisa de uma integracao especifica? Me conta o que usa hoje!"""

    # Interesse/quero contratar
    elif any(palavra in content_lower for palavra in ["quero", "gostaria", "contratar", "comecar", "interesse", "interessado", "demo", "demonstracao", "testar"]):
        return """Otimo! Vamos comecar!

Para preparar uma proposta personalizada, preciso de algumas informacoes:

1. Qual seu WhatsApp ou email para contato?
2. Qual o segmento da sua empresa?
3. Quantos atendentes voce tem hoje?
4. Quais canais usa atualmente (WhatsApp, site, etc)?

Ou se preferir, me passe apenas seu WhatsApp que nossa equipe entra em contato em ate 2 horas!

Estamos prontos para transformar seu atendimento!"""

    # Resposta generica
    else:
        return f"""Vi que voce quer saber sobre: "{content}"

A AIpraTI oferece:
- Chatbots inteligentes para WhatsApp, Telegram e Web
- Automacao de atendimento com IA
- Qualificacao automatica de leads
- Chatwoot para equipes (varios atendentes, 1 numero)
- Integracoes com CRM e sistemas

Me diga o que procura:
- "chatbot" - Nossos bots inteligentes
- "chatwoot" - Plataforma de atendimento em equipe
- "precos" - Planos e valores
- "leads" - Qualificacao automatica
- "integracoes" - Sistemas que conectamos

Ou me passe seu WhatsApp que nossa equipe liga pra voce!"""
