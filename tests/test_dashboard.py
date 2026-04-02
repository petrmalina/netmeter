"""Tests for netmeter.dashboard module."""

from unittest import mock


def test_sanitize_filename():
    """sanitize_filename should replace special characters."""
    from netmeter.dashboard import sanitize_filename

    assert sanitize_filename("My WiFi") == "My_WiFi"
    assert sanitize_filename("net-work_1") == "net-work_1"
    assert sanitize_filename("café/réseau") == "café_réseau"
    assert sanitize_filename("") == ""


def test_generate_graph_empty_data():
    """generate_graph should return False for empty timestamps."""
    from netmeter.dashboard import generate_graph

    data = {"timestamps": [], "downloads": [], "uploads": [], "pings": []}
    period = {"name": "24h", "label": "Last 24 hours", "hours": 24, "aggregate": None}

    result = generate_graph(data, "TestNet", period, "/tmp/test.png")
    assert result is False


def test_generate_graph_creates_file(tmp_path):
    """generate_graph should create a PNG file when data is available."""
    from datetime import datetime, timedelta

    from netmeter.dashboard import generate_graph

    now = datetime.now()
    timestamps = [now - timedelta(hours=i) for i in range(5, 0, -1)]
    data = {
        "timestamps": timestamps,
        "downloads": [50.0, 60.0, 55.0, 70.0, 65.0],
        "uploads": [10.0, 12.0, 11.0, 15.0, 13.0],
        "pings": [20.0, 18.0, 22.0, 19.0, 21.0],
    }
    period = {"name": "24h", "label": "Last 24 hours", "hours": 24, "aggregate": None}
    output_path = str(tmp_path / "test_graph.png")

    result = generate_graph(data, "TestNet", period, output_path)

    assert result is True
    assert (tmp_path / "test_graph.png").exists()
    assert (tmp_path / "test_graph.png").stat().st_size > 0


def test_generate_dashboard_no_db(tmp_path):
    """generate_dashboard should print message when DB doesn't exist."""
    with (
        mock.patch("netmeter.dashboard.DB_PATH", tmp_path / "nonexistent.db"),
        mock.patch("builtins.print") as mock_print,
    ):
        from netmeter.dashboard import generate_dashboard

        generate_dashboard()

    mock_print.assert_called_with("No database found. Run a measurement first.")
