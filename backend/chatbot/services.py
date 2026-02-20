import os
import logging
import requests
import json

logger = logging.getLogger(__name__)

def get_ai_response(history, system_prompt):
    """
    Consome a API do OpenRouter via requests puro para evitar erros de tipagem.
    """
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        # URL fixa do OpenRouter para Chat Completions
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-chat')

        if not api_key:
            logger.error("API Key do OpenRouter não configurada.")
            return "Erro de configuração: Chave da API ausente."

        # Monta as mensagens
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history:
            # Garante que sender seja string
            sender_role = "assistant" if str(msg.sender) == 'bot' else "user"
            content = str(msg.text) if msg.text else ""
            if content:
                messages.append({"role": sender_role, "content": content})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000", # Necessário para OpenRouter
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7
        }

        logger.info(f"Enviando request RAW para OpenRouter...")
        
        # Chamada direta
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Erro na API da IA: {response.status_code} - {response.text}")
            return "Desculpe, meu cérebro está temporariamente fora do ar."

        response_json = response.json()
        
        # Extração manual e segura do JSON
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            logger.error(f"Formato inesperado do OpenRouter: {response_json}")
            return "Recebi uma resposta vazia da IA."

    except Exception as e:
        logger.error(f"Erro Crítico no requests: {e}", exc_info=True)
        return "Erro técnico interno ao processar sua mensagem."

# Mantemos o envio para o Chatwoot aqui também, usando requests
def send_message_to_channel(channel, conversation_id, text):
    # (Seu código de envio para canais específicos, se houver)
    pass
