# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Docker pull instructions appended to GitHub Release notes automatically
- `docker-compose.yml` attached as a downloadable release asset

### Changed

- Default measurement interval from 10 minutes (600s) to 5 minutes (300s)

## [1.1.0] — 2026-04-02

### Fixed (post-release)

- Release workflow using `--notes-file` instead of inline `--notes` to handle backticks and special characters in changelog

### Added

- Auto-detect WiFi and Ethernet inside Docker via `iwgetid` and `/sys/class/net`
- `wireless-tools` and `iproute2` installed in Docker image for host network detection
- Sysfs + `ip route` fallback network detector (`_detect_sysfs`) for `--network host` containers
- Placeholder dashboard page with auto-refresh while waiting for the first measurement
- Custom `_DashboardHandler` serving `dashboard.html` or placeholder from `/`
- Env file creation and `--env-file` passing in macOS and Windows installers
- 11 new tests (46 total, 85%+ coverage)
- Automated release workflow: tag `v*` → GitHub Release with changelog body
- Changelog validation in CI (PRs must update `CHANGELOG.md`)

### Changed

- Default dashboard port from `8080` to `9280` across Dockerfile, README, installers, and `.env.example`
- macOS installer uses `-p 9280:9280` instead of `--network host` (Docker Desktop compatibility)
- Windows installer uses `-p 9280:9280` instead of `--network host` (Docker Desktop compatibility)
- Linux installer unchanged — `--network host` works correctly on native Docker
- Bumped all GitHub Actions to Node.js 24 compatible versions
- Pinned `aquasecurity/trivy-action` to `v0.35.0` (post-security-incident safe release)

### Fixed

- Dashboard showing "Directory listing for /" when no measurements exist yet
- Matplotlib `MPLCONFIGDIR` permission error in Docker (set to `/tmp/matplotlib`)
- Network detection failing in Docker (previously showed "unknown")
- Removed unnecessary Windows admin check (no longer requires host networking)

### Removed

- Hardcoded `NETMETER_NETWORK_NAME="Docker"` default from Dockerfile (auto-detection preferred)

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

[1.1.0]: https://github.com/petrmalina/netmeter/releases/tag/v1.1.0
[1.0.0]: https://github.com/petrmalina/netmeter/releases/tag/v1.0.0-release
