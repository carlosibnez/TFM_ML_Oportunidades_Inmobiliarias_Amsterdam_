FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias + Chromium para Selenium
RUN apt-get update && apt-get install -y \
    gcc \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos
COPY scraper/requirements.txt /app/requirements.txt

# Instalar requerimientos de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del scraper
COPY scraper/ /app/

# Variables de entorno para Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Comando por defecto: ejecutar scraper en bucle
CMD ["python", "scraper.py"]
