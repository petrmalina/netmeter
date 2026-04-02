"""Tests for netmeter.scheduler module."""

import signal
import threading
from http.server import HTTPServer
from unittest import mock
from urllib.request import urlopen


def test_handle_signal_sets_running_false():
    """Signal handler should set _running to False."""
    import netmeter.scheduler as sched

    sched._running = True
    sched._handle_signal(signal.SIGTERM, None)
    assert sched._running is False


def test_run_scheduler_runs_and_stops():
    """Scheduler should call measure_once and stop on signal."""
    import netmeter.scheduler as sched

    call_count = 0

    def fake_measure():
        nonlocal call_count
        call_count += 1
        sched._running = False

    sched._running = True
    with (
        mock.patch("netmeter.scheduler.measure_once", side_effect=fake_measure),
        mock.patch("netmeter.scheduler.MEASURE_INTERVAL_SECONDS", 0),
        mock.patch("netmeter.scheduler.signal.signal"),
        mock.patch("netmeter.scheduler.time.sleep"),
    ):
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            sched.run_scheduler()
        assert exc_info.value.code == 0
    assert call_count == 1


def test_run_scheduler_handles_exceptions():
    """Scheduler should continue after unexpected exceptions."""
    import netmeter.scheduler as sched

    call_count = 0

    def failing_measure():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("boom")
        sched._running = False

    sched._running = True
    with (
        mock.patch("netmeter.scheduler.measure_once", side_effect=failing_measure),
        mock.patch("netmeter.scheduler.MEASURE_INTERVAL_SECONDS", 0),
        mock.patch("netmeter.scheduler.signal.signal"),
        mock.patch("netmeter.scheduler.time.sleep"),
    ):
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            sched.run_scheduler()
        assert exc_info.value.code == 0
    assert call_count == 2


def test_dashboard_handler_serves_placeholder_when_no_dashboard(tmp_path):
    """Handler should return placeholder HTML when dashboard.html doesn't exist."""
    import functools

    import netmeter.scheduler as sched

    with mock.patch.object(sched, "OUTPUT_DIR", tmp_path):
        handler_cls = functools.partial(sched._DashboardHandler, directory=str(tmp_path))
        server = HTTPServer(("127.0.0.1", 0), handler_cls)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            resp = urlopen(f"http://127.0.0.1:{port}/")
            body = resp.read().decode()
            assert "Waiting for the first measurement" in body
            assert resp.status == 200
        finally:
            server.shutdown()


def test_dashboard_handler_serves_dashboard_html(tmp_path):
    """Handler should serve dashboard.html when it exists."""
    import functools

    import netmeter.scheduler as sched

    dashboard = tmp_path / "dashboard.html"
    dashboard.write_text("<html><body>Real Dashboard</body></html>")

    with mock.patch.object(sched, "OUTPUT_DIR", tmp_path):
        handler_cls = functools.partial(sched._DashboardHandler, directory=str(tmp_path))
        server = HTTPServer(("127.0.0.1", 0), handler_cls)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            resp = urlopen(f"http://127.0.0.1:{port}/")
            body = resp.read().decode()
            assert "Real Dashboard" in body
        finally:
            server.shutdown()


def test_start_dashboard_server_returns_none_when_disabled():
    """Server should not start when port is 0."""
    import netmeter.scheduler as sched

    with mock.patch.object(sched, "DASHBOARD_PORT", 0):
        result = sched._start_dashboard_server()
        assert result is None


def test_start_dashboard_server_starts_on_configured_port(tmp_path):
    """Server should start and be reachable when port is configured."""
    import netmeter.scheduler as sched

    with (
        mock.patch.object(sched, "DASHBOARD_PORT", 0),
        mock.patch.object(sched, "DASHBOARD_HOST", "127.0.0.1"),
        mock.patch.object(sched, "OUTPUT_DIR", tmp_path),
    ):
        sched.DASHBOARD_PORT = 9123
        server = sched._start_dashboard_server()
        assert server is not None
        try:
            resp = urlopen("http://127.0.0.1:9123/")
            assert resp.status == 200
        finally:
            server.shutdown()
