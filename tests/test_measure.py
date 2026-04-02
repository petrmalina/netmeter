"""Tests for netmeter.measure module."""

from unittest import mock


def test_run_speedtest_returns_structured_data():
    """run_speedtest should return a dict with expected keys."""
    mock_results = {
        "download": 100_000_000,
        "upload": 50_000_000,
        "ping": 15.5,
        "server": {"sponsor": "TestISP", "country": "US"},
    }

    with mock.patch("netmeter.measure.speedtest") as mock_st:
        instance = mock.Mock()
        instance.results.dict.return_value = mock_results
        mock_st.Speedtest.return_value = instance

        from netmeter.measure import run_speedtest

        result = run_speedtest()

    assert result["download_mbps"] == 100.0
    assert result["upload_mbps"] == 50.0
    assert result["ping_ms"] == 15.5
    assert result["server_name"] == "TestISP"
    assert result["server_country"] == "US"
    assert "raw_json" in result


def test_run_speedtest_missing_server():
    """Should handle missing server info gracefully."""
    mock_results = {
        "download": 80_000_000,
        "upload": 40_000_000,
        "ping": 20.0,
    }

    with mock.patch("netmeter.measure.speedtest") as mock_st:
        instance = mock.Mock()
        instance.results.dict.return_value = mock_results
        mock_st.Speedtest.return_value = instance

        from netmeter.measure import run_speedtest

        result = run_speedtest()

    assert result["server_name"] == ""
    assert result["server_country"] == ""
