# Cursos Bot - Status de Implantação ✅

Data: 2026-01-26  
Status: **PRONTO PARA INTEGRAÇÃO COM CHATWOOT**

## ✅ Concluído

### 1. **Scraping & Database**
- ✅ Web scraper implementado com BeautifulSoup4
- ✅ 96 cursos da Unifatecie salvos no banco de dados
- ✅ 3 tipos de cursos: Bacharelado, Licenciatura, Tecnológico
- ✅ Comando `python manage.py scrape_cursos` funcional

### 2. **REST API**
- ✅ Endpoint `GET /api/v1/cursos/listar/` retorna lista de cursos
- ✅ Suporta filtro por tipo: `/api/v1/cursos/listar/?tipo=bacharelado`
- ✅ Status HTTP 200 com JSON de resposta

```bash
# Exemplo de resposta
curl https://api.aiprati.com.br/api/v1/cursos/listar/
{
  "total": 96,
  "cursos": [
    {
      "id": 192,
      "nome": "Administração",
      "tipo": "bacharelado",
      "duracao": "4 anos"
    },
    ...
  ]
}
```

### 3. **Webhook Chatwoot**
- ✅ Endpoint `POST /api/v1/cursos/webhook/` implementado
- ✅ Validação de token: `X-Chatwoot-Bot-Token: GAHVm8uAy6jN5rLofcDoqvib`
- ✅ Processamento de mensagens:
  - Busca por keywords (engenharia, administração, pedagogia, etc)
  - Fallback para resposta via IA (OpenRouter)
  - Formatação de resposta com emojis
- ✅ Status 401 se token inválido
- ✅ Status 500 com detalhes se falha na resposta

### 4. **Integração com IA**
- ✅ OpenRouter API integrado para respostas inteligentes
- ✅ System prompt em português (persona de vendedor)
- ✅ Fallback automático se keyword matching falhar

### 5. **Infraestrutura**
- ✅ App Django registrado em `INSTALLED_APPS`
- ✅ Rotas configuradas em `core/urls.py`
- ✅ Banco PostgreSQL com migrations aplicadas
- ✅ Docker image rebuilda com `beautifulsoup4`

## 🔄 Como Integrar com Chatwoot

### Passo 1: Acessar Configurações do Chatwoot
1. Ir para **Settings → Automation → Agent Bots**
2. Clicar em **Add Agent Bot**

### Passo 2: Configurar o Bot
- **Bot Name:** Cursos Bot
- **Bot Type:** Webhook
- **Webhook URL:** `https://api.aiprati.com.br/api/v1/cursos/webhook/`
- **Custom headers:** (deixar em branco, token será validado no body)

### Passo 3: Ativar para Inbox
1. Ir para **Settings → Inboxes**
2. Selecionar o inbox (ex: Chatwoot)
3. Em **Agent Bots**, ativar "Cursos Bot"
4. Salvar

### Passo 4: Testar
Enviar mensagem no Chatwoot:
```
Cliente: "Tem algum curso de engenharia?"
Bot (resposta esperada): 
"✨ Encontrei 5 cursos de Engenharia na Unifatecie:

👨‍🎓 Engenharia Civil - Bacharelado (5 anos)
👨‍🎓 Engenharia Mecânica - Bacharelado (5 anos)
👨‍🎓 Engenharia Elétrica - Bacharelado (5 anos)
👨‍🎓 Engenharia de Software - Bacharelado (4 anos)
👨‍🎓 Engenharia de Produção - Bacharelado (5 anos)

Deseja mais informações sobre algum desses cursos? 🎓"
```

## 📊 Cursos Disponíveis

| Tipo | Quantidade | Exemplos |
|------|-----------|----------|
| Bacharelado | 34 | Administração, Engenharia Civil, Psicologia, Direito |
| Licenciatura | 30 | Pedagogia, Matemática, História, Português |
| Tecnológico | 32 | Análise de Sistemas, Design Gráfico, Gestão RH |

## 🧪 Teste Local (sem Chatwoot)

### Buscar Cursos Específicos
```bash
# Todos os cursos
curl https://api.aiprati.com.br/api/v1/cursos/listar/

# Apenas bacharelados
curl https://api.aiprati.com.br/api/v1/cursos/listar/?tipo=bacharelado

# Apenas licenciaturas
curl https://api.aiprati.com.br/api/v1/cursos/listar/?tipo=licenciatura

# Apenas tecnológicos
curl https://api.aiprati.com.br/api/v1/cursos/listar/?tipo=tecnologico
```

### Testar Processamento de Mensagem (Shell Django)
```bash
docker compose exec bot_django python manage.py shell_plus
```

```python
from cursos_bot.services import processar_mensagem_cursos

# Teste 1: Busca por engenharia
resposta = processar_mensagem_cursos("Quais cursos de engenharia vocês têm?")
print(resposta)

# Teste 2: Busca genérica
resposta = processar_mensagem_cursos("Que cursos vocês oferecem?")
print(resposta)

# Teste 3: Busca específica
resposta = processar_mensagem_cursos("Me mostre licenciaturas")
print(resposta)
```

## 🔧 Troubleshooting

### Webhook retorna 404 ao enviar resposta
**Causa:** Account ID ou Conversation ID não existem no Chatwoot  
**Solução:** Só teste após configurar o bot no Chatwoot e enviar mensagem real

### Webhook retorna 401
**Causa:** Token inválido  
**Solução:** Verificar se `X-Chatwoot-Bot-Token: GAHVm8uAy6jN5rLofcDoqvib` está no header

### Cursos não aparecem
**Causa:** Migration não rodou  
**Solução:** 
```bash
docker compose exec bot_django python manage.py migrate cursos_bot
```

### Scraper falha
**Causa:** Site da Unifatecie pode ter estrutura HTML mudada  
**Solução:** Atualizar lógica do scraper em `backend/cursos_bot/scraper.py`

## 📁 Arquivos da App

```
backend/cursos_bot/
├── __init__.py
├── admin.py                    # Admin interface para gerenciar cursos
├── apps.py
├── models.py                   # Modelo Curso
├── scraper.py                  # Web scraper (BeautifulSoup4)
├── services.py                 # Processamento de mensagens + IA
├── views.py                    # Webhook + REST endpoints
├── urls.py                     # Rotas da app
├── management/
│   └── commands/
│       └── scrape_cursos.py    # Management command para scraping
└── migrations/
    └── 0001_initial.py         # Migration do modelo Curso
```

## 📝 Variáveis de Ambiente Necessárias

```bash
# .env (já configurado)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=deepseek/deepseek-chat
CHATWOOT_BOT_TOKEN=GAHVm8uAy6jN5rLofcDoqvib
CHATWOOT_ACCESS_TOKEN=EvZGb4rPXHH3ccLEiNmoSDLq
CHATWOOT_BASE_URL=https://chat.aiprati.com.br
CHATWOOT_ACCOUNT_ID=1
```

## 🚀 Próximos Passos

1. ✅ Confirmar integração com Chatwoot (configure o bot lá)
2. ⏳ Adicionar link de matrícula aos cursos (campo `link_matricula`)
3. ⏳ Implementar comando `/cursos [termo]` no Chatwoot
4. ⏳ Adicionar log de consultas para analytics
5. ⏳ Cache de cursos com Redis (para acelerar buscas)

## 📞 Suporte

Erros e logs:
```bash
# Ver logs do Django
docker compose logs -f bot_django

# Ver logs da busca/IA
docker compose exec bot_django tail -f /var/log/django.log

# Testar conexão Chatwoot
curl -H "api_access_token: $CHATWOOT_ACCESS_TOKEN" \
  https://chat.aiprati.com.br/api/v1/accounts/1/agents
```

---
**Deploy concluído com sucesso em 26/01/2026 06:27 UTC**
