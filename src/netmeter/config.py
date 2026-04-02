"""Centralized configuration loaded from environment variables (12-factor)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

BASE_DIR = Path(os.environ.get("NETMETER_BASE_DIR", Path(__file__).resolve().parent.parent.parent))

DB_DIR = Path(os.environ.get("NETMETER_DB_DIR", BASE_DIR / "data"))
DB_PATH = DB_DIR / os.environ.get("NETMETER_DB_NAME", "speedtest.db")

OUTPUT_DIR = Path(os.environ.get("NETMETER_OUTPUT_DIR", BASE_DIR / "output"))

MEASURE_INTERVAL_SECONDS = int(os.environ.get("NETMETER_INTERVAL", "600"))
MEASURE_RETRIES = int(os.environ.get("NETMETER_RETRIES", "3"))
MEASURE_RETRY_DELAY = int(os.environ.get("NETMETER_RETRY_DELAY", "15"))

LOG_LEVEL = os.environ.get("NETMETER_LOG_LEVEL", "INFO").upper()

NETWORK_NAME_OVERRIDE = os.environ.get("NETMETER_NETWORK_NAME", "")

GRAPH_DPI = int(os.environ.get("NETMETER_GRAPH_DPI", "120"))

DASHBOARD_PORT = int(os.environ.get("NETMETER_DASHBOARD_PORT", "0"))
DASHBOARD_HOST = os.environ.get("NETMETER_DASHBOARD_HOST", "0.0.0.0")


class Period(TypedDict):
    name: str
    label: str
    hours: int
    aggregate: str | None


PERIODS: list[Period] = [
    {"name": "24h", "label": "Last 24 hours", "hours": 24, "aggregate": None},
    {"name": "7d", "label": "Last 7 days", "hours": 168, "aggregate": "hour"},
    {"name": "30d", "label": "Last 30 days", "hours": 720, "aggregate": "day"},
]

NETWORK_TYPE_LABELS = {"wifi": "WiFi", "ethernet": "Ethernet", "unknown": "Unknown"}
