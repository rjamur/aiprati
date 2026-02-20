"""
Views para o bot de cursos (webhook integrado com Chatwoot)
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import requests
import os

from .services import processar_mensagem_cursos
from .models import Curso
from bots.services import validate_bot_token, record_bot_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_cursos(request):
    """
    Webhook para receber mensagens do Chatwoot e responder sobre cursos
    Validação de token via AgentBot database
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'reason': 'invalid_json'}, status=400)
    
    # Validar token do bot contra banco de dados
    auth_header = request.META.get('HTTP_X_CHATWOOT_BOT_TOKEN')
    is_valid, bot = validate_bot_token(auth_header)
    
    if not is_valid:
        logger.warning(f"Token inválido ou ausente: {auth_header[:10] if auth_header else 'None'}...")
        return JsonResponse({'status': 'error', 'reason': 'invalid_token'}, status=401)
    
    # Registrar requisição
    record_bot_request(bot)
    
    # Extrair dados da mensagem
    event = data.get('event')
    message_type = data.get('message_type')
    
    # Apenas processar mensagens recebidas (não outgoing)
    if event != 'message_created' or message_type != 'incoming':
        return JsonResponse({'status': 'ignored', 'reason': 'not_incoming_message'})
    
    try:
        conversation_id = data.get('conversation', {}).get('id')
        message_content = data.get('content', '').strip()
        account_id = data.get('account', {}).get('id')
        
        if not conversation_id or not message_content or not account_id:
            return JsonResponse({'status': 'ignored', 'reason': 'missing_data'})
        
        # Processar mensagem e gerar resposta
        resposta = processar_mensagem_cursos(message_content)
        
        # Enviar resposta para Chatwoot
        enviado = enviar_resposta_chatwoot(
            conversation_id=conversation_id,
            resposta=resposta,
            account_id=account_id
        )
        
        if enviado:
            logger.info(f"Bot {bot.name} processou requisição com sucesso")
            return JsonResponse({'status': 'success', 'message': 'Resposta enviada', 'bot': bot.name})
        else:
            return JsonResponse({'status': 'error', 'reason': 'failed_to_send'}, status=500)
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook de {bot.name}: {e}")
        return JsonResponse({'status': 'error', 'reason': str(e)}, status=500)


def enviar_resposta_chatwoot(conversation_id, resposta, account_id):
    """
    Envia resposta para o Chatwoot via API
    """
    base_url = os.environ.get('CHATWOOT_BASE_URL')
    access_token = os.environ.get('CHATWOOT_ACCESS_TOKEN')
    
    if not base_url or not access_token:
        logger.error("CHATWOOT_BASE_URL ou CHATWOOT_ACCESS_TOKEN não configurados")
        return False
    
    url = f"{base_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    
    headers = {
        'api_access_token': access_token,
        'Content-Type': 'application/json',
    }
    
    payload = {
        'content': resposta,
        'message_type': 'outgoing',
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            logger.info(f"Resposta enviada para conversa {conversation_id}")
            return True
        else:
            logger.error(f"Erro ao enviar resposta: {response.status_code} - {response.text}")
            return False
    
    except requests.RequestException as e:
        logger.error(f"Erro de conexão ao enviar resposta: {e}")
        return False


@require_http_methods(["GET"])
def listar_cursos(request):
    """
    Endpoint para listar todos os cursos (GET)
    Útil para debug e interface web
    """
    tipo = request.GET.get('tipo')
    
    queryset = Curso.objects.all()
    
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    
    cursos = list(queryset.values('id', 'nome', 'tipo', 'duracao'))
    
    return JsonResponse({
        'total': queryset.count(),
        'cursos': cursos
    })
