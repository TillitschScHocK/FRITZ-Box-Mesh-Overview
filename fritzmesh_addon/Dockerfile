ARG BUILD_FROM
FROM $BUILD_FROM

# Chrome und Dependencies installieren
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Python installieren falls nicht vorhanden
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver installieren (kompatible Version)
RUN CHROMEDRIVER_VERSION=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE) && \
    wget -O /tmp/chromedriver.zip "https://edgedl.me.gstatic.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /tmp && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver* && \
    chmod +x /usr/bin/chromedriver

# Arbeitsverzeichnis
WORKDIR /app

# Python-Dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# App-Dateien kopieren
COPY main.py .
COPY run.sh .
RUN chmod +x run.sh

# Static-Ordner erstellen
RUN mkdir -p /app/static

# Port freigeben
EXPOSE 8000

# Startskript
CMD ["/app/run.sh"]
