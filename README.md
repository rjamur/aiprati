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
