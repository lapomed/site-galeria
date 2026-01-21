# --- Stage 1: Frontend Build ---
FROM node:20-slim AS frontend-builder
WORKDIR /app

# Copia arquivos do npm de lapomed/static_src
COPY lapomed/static_src/package*.json ./lapomed/static_src/
WORKDIR /app/lapomed/static_src
RUN npm install

# Copia o restante dos arquivos para o build do Tailwind
WORKDIR /app
COPY . .
WORKDIR /app/lapomed/static_src
RUN npm run build

# --- Stage 2: Python Runtime ---
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=4008
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Instala o UV
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*

# Copia o lockfile e o arquivo de projeto
COPY pyproject.toml uv.lock ./

# Instala as dependências usando uv
# Nota: Instalando no ambiente virtual do uv dentro do container
RUN uv sync --frozen --no-dev

# Copia os arquivos do projeto
COPY . .

# Copia os assets compilados do stage anterior (ajustado para o caminho correto)
COPY --from=frontend-builder /app/lapomed/static/css/dist/styles.css ./lapomed/static/css/dist/styles.css

# Expõe a porta do Django
EXPOSE 4008

# Comando de execução
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:4008"]
