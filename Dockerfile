FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt . \
    && find /install -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

FROM python:3.12-slim

LABEL org.opencontainers.image.title="NetMeter" \
      org.opencontainers.image.description="Automated internet speed monitoring with per-network tracking and dashboard" \
      org.opencontainers.image.url="https://github.com/petrmalina/netmeter" \
      org.opencontainers.image.source="https://github.com/petrmalina/netmeter" \
      org.opencontainers.image.documentation="https://github.com/petrmalina/netmeter#readme" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.authors="Petr Malina"

RUN apt-get update \
    && apt-get install -y --no-install-recommends wireless-tools iproute2 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r netmeter && useradd -r -g netmeter -s /sbin/nologin netmeter \
    && mkdir -p /app/data /app/output \
    && chown -R netmeter:netmeter /app

COPY --from=builder /install /usr/local

WORKDIR /app
USER netmeter

ENV NETMETER_DB_DIR=/app/data \
    NETMETER_OUTPUT_DIR=/app/output \
    NETMETER_INTERVAL=600 \
    NETMETER_LOG_LEVEL=INFO \
    NETMETER_DASHBOARD_PORT=9280 \
    MPLCONFIGDIR=/tmp/matplotlib

EXPOSE 9280

HEALTHCHECK --interval=60s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9280/')" || exit 1

ENTRYPOINT ["python", "-m", "netmeter"]
