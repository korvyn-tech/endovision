FROM python:3.12-slim

# Instala dependências de sistema mínimas para OpenCV headless e Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências de produção
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte e frontend
COPY pyproject.toml .
COPY backend/ backend/
COPY frontend/ frontend/

# Instala o pacote endovision em modo produção
RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend/src
ENV DATABASE_URL=sqlite:////app/data/endovision.db

CMD ["uvicorn", "endovision.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
