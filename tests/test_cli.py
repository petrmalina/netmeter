"""Tests for netmeter.cli module."""

from unittest import mock


def test_setup_logging_configures_handler():
    """setup_logging should not raise and should be callable."""
    from netmeter.cli import setup_logging

    setup_logging()


def test_measure_once_skips_unknown_network():
    """measure_once should return early when no network is detected."""
    unknown = {"network_name": "unknown", "network_type": "unknown", "interface": "unknown"}
    with (
        mock.patch("netmeter.cli.init_db"),
        mock.patch("netmeter.cli.get_network_info", return_value=unknown),
        mock.patch("netmeter.cli.run_speedtest") as mock_speed,
    ):
        from netmeter.cli import measure_once

        measure_once()
        mock_speed.assert_not_called()


def test_measure_once_runs_full_cycle(tmp_path):
    """measure_once should test, save, and regenerate dashboard."""
    network = {"network_name": "TestNet", "network_type": "wifi", "interface": "wlan0"}
    speed = {
        "download_mbps": 50.0,
        "upload_mbps": 10.0,
        "ping_ms": 20.0,
        "server_name": "S",
        "server_country": "US",
        "raw_json": "{}",
    }
    with (
        mock.patch("netmeter.cli.init_db"),
        mock.patch("netmeter.cli.get_network_info", return_value=network),
        mock.patch("netmeter.cli.run_speedtest", return_value=speed),
        mock.patch("netmeter.cli.save_measurement") as mock_save,
        mock.patch("netmeter.cli.generate_dashboard") as mock_dash,
    ):
        from netmeter.cli import measure_once

        measure_once()
        mock_save.assert_called_once_with(network, speed)
        mock_dash.assert_called_once()


def test_measure_once_retries_on_failure():
    """measure_once should retry on SpeedtestException."""
    import speedtest

    network = {"network_name": "RetryNet", "network_type": "wifi", "interface": "wlan0"}
    speed = {
        "download_mbps": 50.0,
        "upload_mbps": 10.0,
        "ping_ms": 20.0,
        "server_name": "",
        "server_country": "",
        "raw_json": "{}",
    }
    with (
        mock.patch("netmeter.cli.init_db"),
        mock.patch("netmeter.cli.get_network_info", return_value=network),
        mock.patch(
            "netmeter.cli.run_speedtest",
            side_effect=[speedtest.SpeedtestException("fail"), speed],
        ),
        mock.patch("netmeter.cli.save_measurement"),
        mock.patch("netmeter.cli.generate_dashboard"),
        mock.patch("netmeter.cli.time.sleep"),
        mock.patch("netmeter.cli.MEASURE_RETRIES", 2),
        mock.patch("netmeter.cli.MEASURE_RETRY_DELAY", 0),
    ):
        from netmeter.cli import measure_once

        measure_once()


def test_measure_once_exits_after_max_retries():
    """measure_once should sys.exit(1) after exhausting retries."""
    import speedtest

    network = {"network_name": "FailNet", "network_type": "wifi", "interface": "wlan0"}
    with (
        mock.patch("netmeter.cli.init_db"),
        mock.patch("netmeter.cli.get_network_info", return_value=network),
        mock.patch("netmeter.cli.run_speedtest", side_effect=speedtest.SpeedtestException("fail")),
        mock.patch("netmeter.cli.time.sleep"),
        mock.patch("netmeter.cli.MEASURE_RETRIES", 2),
        mock.patch("netmeter.cli.MEASURE_RETRY_DELAY", 0),
    ):
        import pytest

        from netmeter.cli import measure_once

        with pytest.raises(SystemExit) as exc_info:
            measure_once()
        assert exc_info.value.code == 1


def test_run_dashboard_calls_generate():
    """run_dashboard should call generate_dashboard."""
    with mock.patch("netmeter.cli.generate_dashboard") as mock_gen:
        from netmeter.cli import run_dashboard

        run_dashboard()
        mock_gen.assert_called_once()


def test_main_dispatches_dashboard():
    """main should dispatch to run_dashboard when argv[1] is 'dashboard'."""
    with (
        mock.patch("sys.argv", ["netmeter", "dashboard"]),
        mock.patch("netmeter.cli.run_dashboard") as mock_dash,
    ):
        from netmeter.cli import main

        main()
        mock_dash.assert_called_once()


def test_main_dispatches_measure():
    """main should dispatch to measure_once by default."""
    with (
        mock.patch("sys.argv", ["netmeter"]),
        mock.patch("netmeter.cli.measure_once") as mock_measure,
    ):
        from netmeter.cli import main

        main()
        mock_measure.assert_called_once()
