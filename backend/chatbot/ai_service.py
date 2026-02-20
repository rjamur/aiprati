import os
from openai import OpenAI

def gerar_resposta_ia(historico_mensagens):
    """
    Recebe uma lista de mensagens e retorna a resposta do OpenRouter.
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )

    # Prompt do Sistema (A Personalidade)
    mensagens = [
        {"role": "system", "content": "Você é um assistente útil e direto de uma organização social. Responda com clareza."}
    ]
    
    # Adiciona o histórico da conversa
    mensagens.extend(historico_mensagens)

    try:
        completion = client.chat.completions.create(
            model=os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-chat"),
            messages=mensagens
        )
        # Extração segura da resposta
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Erro no OpenRouter: {e}")
        return "Desculpe, estou reorganizando meus pensamentos. Tente novamente."
