# fusion

---

## Instruções de Deploy na VM (Ubuntu)

Este guia detalha os passos para configurar e rodar este projeto em um servidor Ubuntu limpo (ex: uma instância EC2 na AWS).

### Pré-requisitos

Antes de começar, certifique-se de que os seguintes softwares estão instalados na sua VM:

1.  **Git:** Para clonar o repositório.
    ```bash
    sudo apt-get update
    sudo apt-get install -y git
    ```
2.  **Docker:** Para rodar os contêineres da aplicação.
    ```bash
    # Siga as instruções oficiais para instalar o Docker Engine no Ubuntu:
    # https://docs.docker.com/engine/install/ubuntu/
    ```
3.  **Docker Compose:** Para orquestrar os serviços.
    ```bash
    # Siga as instruções oficiais para instalar o plugin do Docker Compose:
    # https://docs.docker.com/compose/install/
    ```

### Passos para o Deploy

1.  **Clonar o Repositório**
    Clone o projeto do seu repositório Git para a VM.
    ```bash
    git clone https://github.com/seu-usuario/seu-repositorio.git
    cd seu-repositorio
    ```

2.  **Configurar as Variáveis de Ambiente**
    O projeto usa um arquivo `.env` para gerenciar segredos. Crie o seu a partir do arquivo de exemplo.
    ```bash
    cp .env.example .env
    ```
    Agora, edite o arquivo `.env` com um editor de sua preferência (como `nano` ou `vim`) e preencha todas as variáveis com os valores corretos para o seu ambiente de produção.
    ```bash
    nano .env
    ```

3.  **Construir e Iniciar os Serviços**
    Use o Docker Compose para construir as imagens e iniciar todos os contêineres em modo "detached" (`-d`).
    ```bash
    docker-compose up --build -d
    ```

4.  **Verificar o Status**
    Você pode verificar se todos os contêineres estão rodando com `docker-compose ps`. Para visualizar os logs em tempo real do serviço Django, use:
    ```bash
    docker-compose logs -f django
    ```

### Gerenciando os Serviços

- **Parar todos os serviços:** `docker-compose down`
- **Reiniciar os serviços:** `docker-compose restart`



## 🤖 Habilitando o AI Copilot (Captain) com OpenRouter (Bypass Enterprise)

O Chatwoot possui ferramentas nativas de IA no editor de mensagens (reescrever, expandir, resumir) gerenciadas por um motor chamado "Captain". Oficialmente, a interface web exige um plano Enterprise para configurar um provedor customizado. 

Como o foco do projeto é manter a infraestrutura open-source e de baixo custo (ideal para ONGs e pequenos consultórios), utilizamos o método abaixo para injetar as credenciais do **OpenRouter** diretamente no banco de dados. Isso permite o uso de modelos open-source poderosos (como Llama 3 ou DeepSeek) pagando frações de centavos ou utilizando *tiers* gratuitos.

### Instruções de Configuração

1. Acesse o terminal do seu servidor na pasta raiz do projeto (onde está o `docker-compose.yml`).
2. No bloco de código abaixo, substitua `SUA_CHAVE_AQUI` pela sua API Key real do OpenRouter.
3. Execute o comando inteiro. Ele fará a injeção segura no PostgreSQL bypassando o front-end:

```bash
docker compose exec -T db psql -U postgres -d chatwoot_production << 'EOF'
-- 1. Limpa configurações conflitantes anteriores
DELETE FROM installation_configs WHERE name IN ('CAPTAIN_OPEN_AI_API_KEY', 'CAPTAIN_OPEN_AI_MODEL', 'CAPTAIN_OPEN_AI_ENDPOINT');

-- 2. Injeta a configuração do OpenRouter envelopada como JSON String válida para o Ruby
INSERT INTO installation_configs (name, serialized_value, created_at, updated_at, locked) VALUES
('CAPTAIN_OPEN_AI_API_KEY', '"--- !ruby/hash:ActiveSupport::HashWithIndifferentAccess\nvalue: SUA_CHAVE_AQUI\n"', NOW(), NOW(), false),
('CAPTAIN_OPEN_AI_MODEL', '"--- !ruby/hash:ActiveSupport::HashWithIndifferentAccess\nvalue: meta-llama/llama-3-8b-instruct:free\n"', NOW(), NOW(), false),
('CAPTAIN_OPEN_AI_ENDPOINT', '"--- !ruby/hash:ActiveSupport::HashWithIndifferentAccess\nvalue: [https://openrouter.ai/api](https://openrouter.ai/api)\n"', NOW(), NOW(), false);
EOF

4. Após o terminal confirmar as inserções (INSERT 0 3), reinicie o serviço do Chatwoot para recarregar o cache da aplicação:
```bash
docker compose restart chatwoot



