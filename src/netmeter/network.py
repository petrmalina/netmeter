"""Detect the currently active network connection."""

import subprocess
from pathlib import Path

from netmeter.config import NETWORK_NAME_OVERRIDE

_SYSFS_NET = Path("/sys/class/net")
_ARPHRD_ETHER = 1
_ARPHRD_LOOPBACK = 772


def get_network_info() -> dict:
    """Return a dict with network_name, network_type, and interface.

    Detection order:
    1. NETMETER_NETWORK_NAME env override (useful in Docker / headless)
    2. nmcli (NetworkManager)
    3. iwgetid (fallback for WiFi SSID)
    4. sysfs + ip route (works inside Docker with --network host)
    5. Default "unknown"
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

    info = _detect_sysfs()
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


def _get_default_interface() -> str | None:
    """Return the default route interface name via `ip route`."""
    try:
        result = subprocess.run(
            ["ip", "-o", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if "dev" in parts:
                return parts[parts.index("dev") + 1]
    except (subprocess.SubprocessError, FileNotFoundError, IndexError, ValueError):
        pass
    return None


def _is_wireless_interface(iface: str) -> bool:
    """Check if an interface is wireless via /sys/class/net/<iface>/wireless."""
    return (_SYSFS_NET / iface / "wireless").exists()


def _detect_sysfs() -> dict | None:
    """Detect network type via sysfs and ip route (works in Docker --network host)."""
    iface = _get_default_interface()
    if not iface:
        return None

    if _is_wireless_interface(iface):
        return {
            "network_name": f"WiFi ({iface})",
            "network_type": "wifi",
            "interface": iface,
        }

    type_path = _SYSFS_NET / iface / "type"
    try:
        arp_type = int(type_path.read_text().strip())
    except (OSError, ValueError):
        return None

    if arp_type == _ARPHRD_ETHER:
        return {
            "network_name": f"Ethernet ({iface})",
            "network_type": "ethernet",
            "interface": iface,
        }

    return None
