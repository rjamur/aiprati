import requests
import json
import sys

# CORREÇÃO AQUI: Mudamos de 'webhook/bot/' para 'webhook/chatwoot/'
URL_WEBHOOK = "http://localhost:8000/api/v1/webhook/chatwoot/"

def testar_webhook():
    print(f"🚀 Iniciando teste contra: {URL_WEBHOOK}")

    payload = {
        "event": "message_created",
        "message_type": "incoming",
        "content": "Olá! Quero saber como funciona a filiação.",
        "conversation": {"id": 12345},
        "sender": {
            "type": "contact",
            "id": 999,
            "name": "Maria Testadora"
        },
        "id": 888
    }

    try:
        response = requests.post(
            URL_WEBHOOK, 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print("-" * 30)
        print(f"📡 Status Code: {response.status_code}")
        try:
            print(f"📄 Resposta: {response.json()}")
        except:
            print(f"📄 Resposta (Texto): {response.text}")
        print("-" * 30)

    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    testar_webhook()
