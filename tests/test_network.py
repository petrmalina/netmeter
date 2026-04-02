"""Tests for netmeter.network module."""

from unittest import mock


def test_env_override_takes_priority():
    """NETMETER_NETWORK_NAME env var should override auto-detection."""
    with mock.patch("netmeter.network.NETWORK_NAME_OVERRIDE", "CustomNet"):
        from netmeter.network import get_network_info

        info = get_network_info()
        assert info["network_name"] == "CustomNet"
        assert info["network_type"] == "custom"
        assert info["interface"] == "env"


def test_nmcli_wifi_detection():
    """Should detect WiFi via nmcli output."""
    from netmeter.network import _detect_nmcli

    nmcli_output = "wlan0:wifi:connected:MyWiFi\nlo:loopback:connected (externally):lo\n"
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout=nmcli_output, returncode=0)
        result = _detect_nmcli()

    assert result is not None
    assert result["network_name"] == "MyWiFi"
    assert result["network_type"] == "wifi"
    assert result["interface"] == "wlan0"


def test_nmcli_ethernet_detection():
    """Should detect Ethernet via nmcli output."""
    from netmeter.network import _detect_nmcli

    nmcli_output = "eth0:ethernet:connected:Wired Connection 1\n"
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout=nmcli_output, returncode=0)
        result = _detect_nmcli()

    assert result is not None
    assert result["network_name"] == "Wired Connection 1"
    assert result["network_type"] == "ethernet"


def test_nmcli_not_found_returns_none():
    """Should return None when nmcli is not available."""
    from netmeter.network import _detect_nmcli

    with mock.patch("subprocess.run", side_effect=FileNotFoundError):
        result = _detect_nmcli()

    assert result is None


def test_iwgetid_detection():
    """Should detect WiFi SSID via iwgetid."""
    from netmeter.network import _detect_iwgetid

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout="FallbackSSID\n", returncode=0)
        result = _detect_iwgetid()

    assert result is not None
    assert result["network_name"] == "FallbackSSID"
    assert result["network_type"] == "wifi"


def test_iwgetid_empty_returns_none():
    """Should return None when iwgetid returns empty."""
    from netmeter.network import _detect_iwgetid

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout="", returncode=0)
        result = _detect_iwgetid()

    assert result is None


def test_fallback_to_unknown():
    """Should return 'unknown' when all detection methods fail."""
    with (
        mock.patch("netmeter.network.NETWORK_NAME_OVERRIDE", ""),
        mock.patch("netmeter.network._detect_nmcli", return_value=None),
        mock.patch("netmeter.network._detect_iwgetid", return_value=None),
    ):
        from netmeter.network import get_network_info

        info = get_network_info()
        assert info["network_name"] == "unknown"
        assert info["network_type"] == "unknown"


def test_nmcli_colon_in_ssid():
    """Should handle SSIDs containing colons."""
    from netmeter.network import _detect_nmcli

    nmcli_output = "wlan0:wifi:connected:My:Network:Name\n"
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout=nmcli_output, returncode=0)
        result = _detect_nmcli()

    assert result is not None
    assert result["network_name"] == "My:Network:Name"
