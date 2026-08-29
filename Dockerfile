# Dockerfile — AvisCompare API (données + IA)
#
# Construit une image contenant l'API FastAPI complète (données et
# modèle de sentiment), prête à être déployée sur n'importe quel
# hébergeur supportant Docker (Railway, Render, un VPS, etc.).

FROM python:3.12-slim

WORKDIR /app

# Dépendances système nécessaires à psycopg et à la compilation
# de certains paquets Python.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

COPY src/ src/
COPY database/ database/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]