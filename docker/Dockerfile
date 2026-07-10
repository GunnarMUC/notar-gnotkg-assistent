# Dockerfile – Notar GNotKG Assistent
# App im Container, Ollama nativ auf dem Host (Metal-Beschleunigung auf Apple Silicon)

FROM python:3.12-slim-bookworm

LABEL maintainer="Notar GNotKG Assistent"
LABEL description="Lokale, DSGVO-konforme Desktop-App zur Erstellung GNotKG-konformer Honorarrechnungen"

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-deu \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# App-Verzeichnis
WORKDIR /app

# Python-Abhängigkeiten
COPY requirements.txt pyproject.toml* ./
RUN pip install --no-cache-dir -r requirements.txt

# App-Code
COPY core/ ./core/
COPY prompts/ ./prompts/
COPY templates/ ./templates/
COPY data/ ./data/
COPY app.py .

# Streamlit-Port
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# Ollama-Host als Umgebungsvariable (default: host.docker.internal)
ENV OLLAMA_HOST=host.docker.internal:11434

# Streamlit-Konfiguration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=127.0.0.1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Non-Root-User für minimale Rechte im Container
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=127.0.0.1"]
