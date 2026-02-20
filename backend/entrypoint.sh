#!/bin/sh

# Aborta o script se qualquer comando falhar
set -e

# Define o host e a porta do banco de dados a partir de variáveis de ambiente, com defaults
DB_HOST=${POSTGRES_HOST:-postgres}
DB_PORT=${POSTGRES_PORT:-5432}

echo "Aguardando o banco de dados em ${DB_HOST}:${DB_PORT}..."

# Loop até que o banco de dados esteja aceitando conexões
# O comando 'nc' (netcat) tenta se conectar. O loop continua enquanto a conexão falhar.
while ! nc -z ${DB_HOST} ${DB_PORT}; do
  sleep 1
done

echo "Banco de dados pronto!"

# Aplica as migrações do banco de dados
echo "Aplicando migrações do banco de dados..."
python manage.py migrate --noinput

# Coleta arquivos estáticos (admin/css, js) para produção
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Inicia o servidor Gunicorn
# --workers: número de processos para lidar com as requisições.
# --bind: especifica o endereço e a porta. 0.0.0.0 torna acessível de fora do contêiner.
echo "Iniciando o servidor Gunicorn na porta 8000..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3