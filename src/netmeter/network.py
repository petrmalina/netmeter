"""Detect the currently active network connection."""

import subprocess

from netmeter.config import NETWORK_NAME_OVERRIDE


def get_network_info() -> dict:
    """Return a dict with network_name, network_type, and interface.

    Detection order:
    1. NETMETER_NETWORK_NAME env override (useful in Docker / headless)
    2. nmcli (NetworkManager)
    3. iwgetid (fallback for WiFi SSID)
    4. Default "unknown"
    """
    if NETWORK_NAME_OVERRIDE:
        return {
            "network_name": NETWORK_NAME_OVERRIDE,
            "network_type": "custom",
            "interface": "env",
        }

    info = _detect_nmcli()
    if info:
        return info

    info = _detect_iwgetid()
    if info:
        return info

    return {"network_name": "unknown", "network_type": "unknown", "interface": "unknown"}


def _detect_nmcli() -> dict | None:
    """Detect network via NetworkManager CLI."""
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 4 and parts[2] == "connected":
                device = parts[0]
                conn_type = parts[1]
                connection_name = ":".join(parts[3:])
                if conn_type in ("wifi", "ethernet"):
                    return {
                        "network_name": connection_name,
                        "network_type": conn_type,
                        "interface": device,
                    }
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _detect_iwgetid() -> dict | None:
    """Detect WiFi SSID via iwgetid."""
    try:
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        ssid = result.stdout.strip()
        if ssid:
            return {
                "network_name": ssid,
                "network_type": "wifi",
                "interface": "unknown",
            }
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None
