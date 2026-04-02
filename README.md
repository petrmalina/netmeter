# NetMeter

[![CI](https://github.com/petrmalina/netmeter/actions/workflows/ci.yml/badge.svg)](https://github.com/petrmalina/netmeter/actions/workflows/ci.yml)
[![Docker](https://github.com/petrmalina/netmeter/actions/workflows/docker.yml/badge.svg)](https://github.com/petrmalina/netmeter/actions/workflows/docker.yml)
[![GHCR](https://img.shields.io/badge/ghcr.io-petrmalina%2Fnetmeter-blue?logo=github)](https://ghcr.io/petrmalina/netmeter)
[![Image Size](https://ghcr-badge.egpl.dev/petrmalina/netmeter/size)](https://github.com/petrmalina/netmeter/pkgs/container/netmeter)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Automated internet speed monitoring with per-network tracking, comparison dashboard, and Docker support.

## Features

- **Speed testing** — download, upload, and ping via Ookla Speedtest
- **Network detection** — auto-identifies WiFi SSID / Ethernet connection
- **Per-network graphs** — 24h, 7d, 30d charts for each network
- **Network comparison** — side-by-side table with best-value highlighting
- **Dark-theme dashboard** — responsive HTML served on port 8080
- **Docker image** — `ghcr.io/petrmalina/netmeter` (multi-arch: amd64, arm64)
- **Auto-updates** — optional Watchtower integration
- **12-factor config** — all settings via environment variables
- **Service installers** — one-command setup for Linux, macOS, Windows
- **Built-in scheduler** — no cron dependency
- **Retry logic** — automatic retries on speed test failures

## Quick Start

### One command (Docker)

```bash
docker run -d --name netmeter --network host \
  ghcr.io/petrmalina/netmeter:latest
```

Dashboard at **http://localhost:8080**.

### Docker Compose

```bash
cp .env.example .env
docker compose up -d
```

With auto-updates:

```bash
docker compose --profile auto-update up -d
```

### Service Installers

All installers pull the Docker image from `ghcr.io` — no Python installation needed.

```bash
# Linux (systemd) — requires Docker
sudo bash services/install-systemd.sh install

# macOS (launchd) — requires Docker Desktop
bash services/install-macos.sh install

# Windows — requires Docker Desktop, run as Administrator
powershell -ExecutionPolicy Bypass -File services/install-windows.ps1 install
```

To uninstall, replace `install` with `uninstall`.

### Local Development (pip)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e .

netmeter                       # single measurement
netmeter dashboard             # regenerate dashboard
python -m netmeter             # run scheduler
```

## Configuration

All settings via environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
|---|---|---|
| `NETMETER_INTERVAL` | `600` | Measurement interval (seconds) |
| `NETMETER_RETRIES` | `3` | Retry attempts on failure |
| `NETMETER_RETRY_DELAY` | `15` | Delay between retries (seconds) |
| `NETMETER_LOG_LEVEL` | `INFO` | Log level |
| `NETMETER_NETWORK_NAME` | *(auto)* | Override detected network name |
| `NETMETER_DB_DIR` | `./data` | Database directory |
| `NETMETER_DB_NAME` | `speedtest.db` | Database filename |
| `NETMETER_OUTPUT_DIR` | `./output` | Dashboard output directory |
| `NETMETER_GRAPH_DPI` | `120` | Graph resolution |
| `NETMETER_DASHBOARD_PORT` | `0` / `8080` | HTTP port (0=off, 8080 in Docker) |

## Auto-Updates

The systemd service pulls the latest image on every restart. For continuous auto-updates:

**Watchtower (via compose):**

```bash
docker compose --profile auto-update up -d
```

**Manual update:**

```bash
docker pull ghcr.io/petrmalina/netmeter:latest
docker restart netmeter
```

## Development

```bash
pip install -e ".[dev]"

ruff check src/ tests/        # lint
ruff format src/ tests/        # format
mypy src/netmeter/             # type check
pytest --cov=netmeter          # tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## Project Structure

```
netmeter/
├── src/netmeter/              # Python package
│   ├── config.py              # 12-factor configuration
│   ├── cli.py                 # CLI entry points
│   ├── database.py            # SQLite data access
│   ├── dashboard.py           # HTML + graph generation
│   ├── measure.py             # speed test execution
│   ├── network.py             # network detection
│   └── scheduler.py           # scheduler + HTTP server
├── tests/                     # pytest test suite
├── services/                  # OS service installers (Docker-based)
├── Dockerfile                 # multi-stage, non-root, OCI labels
├── docker-compose.yml         # with optional Watchtower
├── .github/workflows/
│   ├── ci.yml                 # lint, typecheck, test
│   └── docker.yml             # build, push ghcr.io, Trivy scan
└── pyproject.toml
```

## Docker Image Labels

| Label | Value |
|---|---|
| `org.opencontainers.image.title` | NetMeter |
| `org.opencontainers.image.description` | Automated internet speed monitoring |
| `org.opencontainers.image.url` | https://github.com/petrmalina/netmeter |
| `org.opencontainers.image.source` | https://github.com/petrmalina/netmeter |
| `org.opencontainers.image.licenses` | MIT |
| `org.opencontainers.image.authors` | Petr Malina |

## License

[MIT](LICENSE)
