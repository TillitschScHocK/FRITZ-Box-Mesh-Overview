ARG BUILD_FROM
FROM ${BUILD_FROM}

# Update und Python-Full installieren (notwendig für venv in Debian 12)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-full \
    python3-venv \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Virtual Environment erstellen (PEP 668 Workaround für Debian 12)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# pip upgrade
RUN pip install --upgrade pip setuptools wheel

# Python-Packages installieren
RUN pip install --no-cache-dir \
    playwright==1.40.0 \
    Flask==3.0.0 \
    Werkzeug==3.0.0

# Playwright Chromium installieren
RUN playwright install chromium

WORKDIR /app

COPY main.py .
COPY run.sh .
RUN chmod +x /app/run.sh && mkdir -p /app/static

EXPOSE 8000

CMD ["/app/run.sh"]
