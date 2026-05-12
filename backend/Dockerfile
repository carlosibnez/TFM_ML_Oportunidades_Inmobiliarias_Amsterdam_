FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY backend/requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY backend/ /app/

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
