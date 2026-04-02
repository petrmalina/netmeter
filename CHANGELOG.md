# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-02

### Added

- Python package (`src/netmeter/`) with CLI entry points
- 12-factor configuration via environment variables
- Built-in scheduler (replaces cron dependency)
- Built-in HTTP dashboard server (`NETMETER_DASHBOARD_PORT`)
- Docker image on `ghcr.io/petrmalina/netmeter` (multi-arch: amd64, arm64)
- Auto-update support via Watchtower
- Service installers for Linux (systemd), macOS (launchd), Windows (Docker)
- Per-network speed graphs (24h, 7d, 30d)
- Network comparison table with best-value highlighting
- Dark-theme responsive HTML dashboard
- Retry logic with configurable attempts and delay
- pytest suite (35 tests, 80%+ coverage)
- GitHub Actions CI (lint, type check, test matrix, Docker build + push)
- Dependabot for pip, GitHub Actions, and Docker
- Trivy security scanning on Docker image
- Issue/PR templates, CONTRIBUTING.md, SECURITY.md

Initial public release.

[1.0.0]: https://github.com/petrmalina/netmeter/releases/tag/v1.0.0
