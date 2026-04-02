"""Tests for netmeter.scheduler module."""

import signal
from unittest import mock


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
