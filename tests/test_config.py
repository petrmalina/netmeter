"""Tests for netmeter.config module."""

import os
from unittest import mock


def test_default_config_values():
    """Default config values should be sensible when no env vars are set."""
    with mock.patch.dict(os.environ, {}, clear=False):
        import importlib

        import netmeter.config as cfg

        importlib.reload(cfg)

        assert cfg.MEASURE_INTERVAL_SECONDS == 600
        assert cfg.MEASURE_RETRIES == 3
        assert cfg.MEASURE_RETRY_DELAY == 15
        assert cfg.LOG_LEVEL == "INFO"
        assert cfg.GRAPH_DPI == 120
        assert cfg.NETWORK_NAME_OVERRIDE == ""


def test_config_from_env():
    """Config should read values from environment variables."""
    env = {
        "NETMETER_INTERVAL": "300",
        "NETMETER_RETRIES": "5",
        "NETMETER_RETRY_DELAY": "30",
        "NETMETER_LOG_LEVEL": "debug",
        "NETMETER_GRAPH_DPI": "200",
        "NETMETER_NETWORK_NAME": "TestNetwork",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        import importlib

        import netmeter.config as cfg

        importlib.reload(cfg)

        assert cfg.MEASURE_INTERVAL_SECONDS == 300
        assert cfg.MEASURE_RETRIES == 5
        assert cfg.MEASURE_RETRY_DELAY == 30
        assert cfg.LOG_LEVEL == "DEBUG"
        assert cfg.GRAPH_DPI == 200
        assert cfg.NETWORK_NAME_OVERRIDE == "TestNetwork"


def test_periods_structure():
    """PERIODS should have correct structure."""
    from netmeter.config import PERIODS

    assert len(PERIODS) == 3
    for period in PERIODS:
        assert "name" in period
        assert "label" in period
        assert "hours" in period
        assert "aggregate" in period
        assert isinstance(period["hours"], int)


def test_network_type_labels():
    """NETWORK_TYPE_LABELS should cover all known types."""
    from netmeter.config import NETWORK_TYPE_LABELS

    assert "wifi" in NETWORK_TYPE_LABELS
    assert "ethernet" in NETWORK_TYPE_LABELS
    assert "unknown" in NETWORK_TYPE_LABELS
