FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV CHRONOS_MODEL_ID=amazon/chronos-2
ENV DEVICE_MAP=cpu
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    openssl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Crear directorio para certificados
RUN mkdir -p /app/certs

EXPOSE 8000

# Script de inicio que genera certificados si no existen y ejecuta uvicorn
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
