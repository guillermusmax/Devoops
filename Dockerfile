# 🥤 NovaLat - Dockerfile
# Sistema de trazabilidad alimentaria para NovaLat

# Usar imagen base de Python 3.11
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN groupadd -r novalat && useradd -r -g novalat novalat

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements-simple.txt requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/

# Crear archivo de configuración básico
RUN echo "DATABASE_URL=postgresql://novalat_user:novalat_pass@postgres:5432/novalat_traceability" > .env && \
    echo "JWT_SECRET_KEY=novalat-secret-key-change-in-production" >> .env && \
    echo "REDIS_URL=redis://redis:6379" >> .env

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/data /app/certs

# Cambiar permisos
RUN chown -R novalat:novalat /app

# Cambiar al usuario no-root
USER novalat

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"] 