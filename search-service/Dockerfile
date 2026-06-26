FROM 185.120.221.119:8083/python:3.12-slim

WORKDIR /app

ENV PIP_INDEX_URL=http://185.120.221.119:8081/repository/pypi-group/simple/
ENV PIP_TRUSTED_HOST=185.120.221.119

ARG NEXUS_URL=http://185.120.221.119:8081

# APT mirror
RUN set -ex \
    && rm -rf /etc/apt/sources.list.d/* \
    && echo "deb ${NEXUS_URL}/repository/debian-13/ trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list \
    && echo "deb ${NEXUS_URL}/repository/debian-13-security/ trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && apt-get update

# Build deps
RUN apt-get update && apt-get install -y gcc curl netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# venv setup
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -vvv 

# Copy app
COPY app/ ./app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Create user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl --fail --silent --show-error http://localhost:8000/health || exit 1