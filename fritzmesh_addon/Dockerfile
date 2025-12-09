ARG BUILD_FROM=python:3.11-slim
FROM ${BUILD_FROM}

# Umgebungsvariablen für Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Systempakete installieren: Chromium, Chromedriver und nötige Libs
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Requirements kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skripte kopieren
COPY . .
RUN chmod +x run.sh

# Port für den Webserver
EXPOSE 8000

# Startbefehl
CMD ["./run.sh"]