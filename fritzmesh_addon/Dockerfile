ARG BUILD_FROM
FROM ${BUILD_FROM}

# Python und minimal Packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Playwright Browser installieren (automatisch heruntergeladen)
RUN pip3 install --no-cache-dir \
    playwright==1.40.0 \
    Flask==3.0.0 \
    Pillow==10.0.0 \
    && python3 -m playwright install chromium

WORKDIR /app

COPY main.py .
COPY run.sh .
RUN chmod +x /app/run.sh && mkdir -p /app/static

EXPOSE 8000

CMD ["/app/run.sh"]
