# Usamos imagen oficial ligera de Python 3.12
FROM python:3.12-slim

# Variables de entorno para que pip no guarde cache y pip use UTF-8
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo requirements.txt primero para cachear instalación
COPY requirements.txt .

# Instalamos las dependencias
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiamos todo el código al contenedor
COPY . .

# Comando por defecto para arrancar el bot
CMD ["python", "chat.py"]
