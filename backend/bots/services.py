"""
Serviços para gerenciar validação de bots
"""
from django.core.cache import cache
from .models import AgentBot
import logging

logger = logging.getLogger(__name__)


def get_bot_by_token(token):
    """
    Busca bot pelo token com cache
    """
    cache_key = f'bot_token:{token}'
    bot = cache.get(cache_key)
    
    if bot is None:
        try:
            bot = AgentBot.objects.get(bot_token=token, is_active=True)
            # Cache por 1 hora
            cache.set(cache_key, bot, 3600)
        except AgentBot.DoesNotExist:
            logger.warning(f"Token inválido ou bot inativo: {token[:10]}...")
            bot = None
    
    return bot


def validate_bot_token(token):
    """
    Valida token e retorna (is_valid, bot)
    """
    if not token:
        return False, None
    
    bot = get_bot_by_token(token)
    
    if bot is None:
        return False, None
    
    return True, bot


def record_bot_request(bot):
    """
    Registra uma requisição do bot
    """
    if bot:
        bot.record_request()
