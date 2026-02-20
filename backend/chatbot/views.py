import json
import requests
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .ai_service import gerar_resposta_ia
from .models import Message

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def chatwoot_webhook(request):
    """
    Lógica Bot vs Humano:
    1. Processar apenas event=message_created e message_type=incoming
    2. Ignorar se já houver assignee (humano) na conversa
    3. Responder apenas se status for open/pending
    4. Se usuário pedir humano/atendente → assign para admin e enviar aviso
    """
    try:
        data = json.loads(request.body)
        
        event = data.get('event')
        message_type = data.get('message_type')
        conversation = data.get('conversation', {}) or {}
        conversation_id = conversation.get('id')
        status = conversation.get('status')
        meta = conversation.get('meta', {}) or {}
        assignee = meta.get('assignee')
        account_id = data.get('account', {}).get('id')
        content = (data.get('content') or '').strip()

        # 1. Validar evento
        if event != 'message_created' or message_type != 'incoming':
            return JsonResponse({'status': 'ignored', 'reason': 'not_incoming_message'})

        # 2. Verificar se há assignee e conteúdo da mensagem
        content_lower = content.lower()
        
        # Se há assignee, só processar se for pergunta sobre cursos/vendas
        if assignee is not None:
            # Permitir bot responder se pergunta sobre cursos
            eh_pergunta_cursos = any(palavra in content_lower for palavra in [
                'curso', 'cursos', 'graduação', 'graduacao', 'formação', 'formacao',
                'bacharelado', 'licenciatura', 'tecnólogo', 'tecnologo',
                'ads', 'administração', 'administracao', 'engenharia', 'pedagogia',
                'direito', 'enfermagem', 'psicologia', 'matemática', 'matematica'
            ])
            
            if not eh_pergunta_cursos:
                logger.info(f"Conversa {conversation_id} ignorada: assignee presente e não é pergunta sobre cursos")
                return JsonResponse({'status': 'ignored', 'reason': 'assigned_and_not_course_question'})
            else:
                logger.info(f"Conversa {conversation_id}: processando pergunta sobre cursos mesmo com assignee")

        # 3. Responder apenas se status for open/pending
        if status not in ('open', 'pending'):
            logger.info(f"Conversa {conversation_id} ignorada: status {status}")
            return JsonResponse({'status': 'ignored', 'reason': f'status_{status}'})

        if not conversation_id or not account_id or not content:
            return JsonResponse({'status': 'ignored', 'reason': 'missing_data'})

        # 4. Detectar pedido de atendimento humano (palavras explícitas)
        if any(palavra in content_lower for palavra in ['humano', 'atendente', 'pessoa', 'operador']):
            admin_id = os.environ.get('CHATWOOT_ADMIN_ID')
            if not admin_id:
                logger.error("CHATWOOT_ADMIN_ID não configurado; handoff impossível")
                return JsonResponse({'status': 'error', 'reason': 'admin_id_missing'}, status=500)

            # Transferir para humano
            assign_to_admin(conversation_id, account_id, admin_id)
            enviar_para_chatwoot(conversation_id, account_id, "Transferindo para um humano...")
            logger.info(f"Conversa {conversation_id} transferida para admin {admin_id}")
            return JsonResponse({'status': 'success', 'action': 'handoff'})

        # 5. Persistir mensagem do usuário
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel='chatwoot',
            sender='user',
            text=content
        )

        # 6. Usar vendas_bot como orquestrador principal
        try:
            from vendas_bot.services import processar_mensagem_vendas
            
            # Preparar histórico para o vendas_bot
            history = Message.objects.filter(
                channel='chatwoot',
                conversation_id=str(conversation_id)
            ).order_by('created_at')
            
            historico_conversa = [
                {"tipo": msg.sender, "conteudo": msg.text}
                for msg in history
            ]
            
            # Usar vendas_bot como orquestrador
            resposta_ia = processar_mensagem_vendas(
                conteudo_mensagem=content,
                nome_usuario=data.get('contact', {}).get('name', 'Cliente'),
                historico_conversa=historico_conversa
            )
            
        except Exception as e:
            logger.error(f"Erro no vendas_bot, usando fallback: {e}")
            # Fallback para IA genérica
            from .ai_service import gerar_resposta_ia
            history = Message.objects.filter(
                channel='chatwoot',
                conversation_id=str(conversation_id)
            ).order_by('created_at')
            
            historico_msgs = [
                {"role": "user" if msg.sender == "user" else "assistant", "content": msg.text}
                for msg in history
            ]
            
            resposta_ia = gerar_resposta_ia(historico_msgs)

        # 7. Persistir resposta do bot
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel='chatwoot',
            sender='bot',
            text=resposta_ia
        )

        # 8. Enviar para Chatwoot
        enviar_para_chatwoot(conversation_id, account_id, resposta_ia)
        
        logger.info(f"Bot respondeu conversa {conversation_id}")
        return JsonResponse({'status': 'success'})

    except requests.HTTPError as e:
        logger.error(f"Erro HTTP ao falar com Chatwoot: {e.response.text if e.response else e}", exc_info=True)
        return JsonResponse({'status': 'error', 'reason': 'chatwoot_http_error'}, status=500)
    except Exception as e:
        logger.error(f"Erro no webhook do Chatwoot: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



def assign_to_admin(conversation_id, account_id, admin_id):
    """Atribui conversa a um agente humano via API do Chatwoot"""
    base_url = os.environ.get("CHATWOOT_BASE_URL")
    token = os.environ.get("CHATWOOT_ACCESS_TOKEN")
    
    url = f"{base_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/assignments"
    headers = {
        "api_access_token": token,
        "Content-Type": "application/json"
    }
    payload = {"assignee_id": admin_id}
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response


def enviar_para_chatwoot(conversation_id, account_id, text):
    """
    Empurra a mensagem da IA para dentro da conversa no Chatwoot via API
    """
    base_url = os.environ.get("CHATWOOT_BASE_URL")
    token = os.environ.get("CHATWOOT_ACCESS_TOKEN")

    url = f"{base_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    
    headers = {
        "api_access_token": token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": text,
        "message_type": "outgoing",
        "private": False 
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code not in [200, 201]:
        logger.error(f"Erro ao enviar para Chatwoot: {response.text}")
    response.raise_for_status()

