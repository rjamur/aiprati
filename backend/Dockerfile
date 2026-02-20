# --- Estágio de Build ---
# Usamos uma imagem completa para ter as ferramentas de compilação necessárias para algumas dependências
FROM python:3.12-slim as builder

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema para compilar pacotes como psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt


# --- Estágio Final/Produção ---
# Usamos uma imagem 'slim' que é muito menor e mais segura
FROM python:3.12-slim

WORKDIR /app

# Cria um usuário e grupo não-root para a aplicação, por segurança
RUN addgroup --system app && adduser --system --group app

# Instala dependências de sistema necessárias para a execução (ex: netcat para o entrypoint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copia as dependências instaladas do estágio de build
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia o código da aplicação
COPY . .

# Garante que o script de entrypoint seja executável
RUN chmod +x /app/entrypoint.sh && \
    chown app:app /app/entrypoint.sh

# Muda a propriedade dos arquivos para o usuário não-root
# Muda a propriedade dos arquivos para o usuário não-root (ANTES de mudar para USER app)
RUN chown -R app:app /app

# Muda para o usuário não-root
# Define o entrypoint que será executado quando o contêiner iniciar
ENTRYPOINT ["/app/entrypoint.sh"]
