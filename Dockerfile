FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY backend/requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY backend/ .

# Cria diretórios necessários
RUN mkdir -p ml/models logs

# Expõe porta
EXPOSE 5000

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Comando de inicialização
CMD ["python", "app.py"]
