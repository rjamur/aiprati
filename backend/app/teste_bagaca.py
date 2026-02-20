import requests
import json
import sys

# --- CONFIGURAÇÃO ---
# Se o seu Docker expõe na porta 8000. Se for outra, ajuste aqui.
# Lembre-se: Definimos a rota como 'webhook/bot/' no urls.py
URL_WEBHOOK = "http://localhost:8000/api/v1/webhook/bot/"

def testar_webhook():
    print(f"🚀 Iniciando teste contra: {URL_WEBHOOK}")

    # Este é o payload exato que o Chatwoot manda quando um cliente fala
    payload = {
        "event": "message_created",
        "message_type": "incoming",       # Importante: se não for incoming, nosso código ignora
        "content": "Olá! Quero saber como funciona a filiação.",
        "conversation": {
            "id": 12345                   # ID fictício para teste
        },
        "sender": {
            "type": "contact",            # Simula um usuário real
            "id": 999,
            "name": "Maria Testadora"
        },
        "id": 888                         # ID da mensagem
    }

    try:
        # Envia o POST
        response = requests.post(
            URL_WEBHOOK, 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10 # Espera até 10s (pois a IA pode demorar um pouco)
        )

        print("-" * 30)
        print(f"📡 Status Code: {response.status_code}")
        
        # Tenta ler a resposta
        try:
            print(f"📄 Resposta: {response.json()}")
        except:
            print(f"📄 Resposta (Texto): {response.text}")
        
        print("-" * 30)

        if response.status_code == 200:
            print("✅ SUCESSO! O Django aceitou, processou a IA e (tentou) devolver ao Chatwoot.")
        elif response.status_code == 404:
            print("❌ ERRO 404: A URL está errada. Verifique o arquivo urls.py.")
        elif response.status_code == 500:
            print("🔥 ERRO 500: O código Python quebrou. Olhe o terminal do Docker!")
        else:
            print("⚠️ Retorno inesperado.")

    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO: O Django está rodando? O Docker está de pé?")
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")

if __name__ == "__main__":
    testar_webhook()
