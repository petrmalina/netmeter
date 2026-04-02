"""Tests for netmeter.database module."""

import sqlite3
from unittest import mock

import pytest


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temporary database directory and patch config."""
    db_dir = tmp_path / "data"
    db_path = db_dir / "speedtest.db"
    with mock.patch("netmeter.database.DB_DIR", db_dir), mock.patch("netmeter.database.DB_PATH", db_path):
        yield db_dir, db_path


def test_init_db_creates_schema(tmp_db):
    """init_db should create the database file and measurements table."""
    from netmeter.database import init_db

    _db_dir, db_path = tmp_db

    init_db()

    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
    assert cursor.fetchone() is not None
    conn.close()


def test_init_db_is_idempotent(tmp_db):
    """Calling init_db twice should not raise."""
    from netmeter.database import init_db

    init_db()
    init_db()


def test_save_and_get_networks(tmp_db):
    """save_measurement should insert data retrievable by get_networks."""
    from netmeter.database import connect, get_networks, init_db, save_measurement

    init_db()

    network_info = {
        "network_name": "TestWiFi",
        "network_type": "wifi",
        "interface": "wlan0",
    }
    speed_data = {
        "download_mbps": 50.0,
        "upload_mbps": 10.0,
        "ping_ms": 20.0,
        "server_name": "TestServer",
        "server_country": "US",
        "raw_json": "{}",
    }

    save_measurement(network_info, speed_data)

    with connect() as conn:
        networks = get_networks(conn)

    assert networks == ["TestWiFi"]


def test_get_network_stats(tmp_db):
    """get_network_stats should return correct averages."""
    from netmeter.database import connect, get_network_stats, init_db, save_measurement

    init_db()

    network_info = {"network_name": "StatsNet", "network_type": "ethernet", "interface": "eth0"}
    for dl, ul, ping in [(100.0, 50.0, 10.0), (80.0, 30.0, 20.0)]:
        save_measurement(
            network_info,
            {
                "download_mbps": dl,
                "upload_mbps": ul,
                "ping_ms": ping,
                "server_name": "",
                "server_country": "",
                "raw_json": "{}",
            },
        )

    with connect() as conn:
        stats = get_network_stats(conn, "StatsNet")

    assert stats["measurement_count"] == 2
    assert abs(stats["avg_download"] - 90.0) < 0.01
    assert abs(stats["avg_upload"] - 40.0) < 0.01
    assert abs(stats["avg_ping"] - 15.0) < 0.01
    assert stats["type"] == "ethernet"


def test_fetch_data_returns_time_series(tmp_db):
    """fetch_data should return timestamps and values for graphing."""
    from netmeter.database import connect, fetch_data, init_db, save_measurement

    init_db()

    network_info = {"network_name": "FetchNet", "network_type": "wifi", "interface": "wlan0"}
    save_measurement(
        network_info,
        {
            "download_mbps": 75.0,
            "upload_mbps": 25.0,
            "ping_ms": 12.0,
            "server_name": "",
            "server_country": "",
            "raw_json": "{}",
        },
    )

    with connect() as conn:
        data = fetch_data(conn, "FetchNet", hours=24, aggregate=None)

    assert len(data["timestamps"]) == 1
    assert data["downloads"][0] == 75.0
    assert data["uploads"][0] == 25.0
    assert data["pings"][0] == 12.0


def test_get_networks_ordered_by_latest(tmp_db):
    """Networks should be ordered by most recent measurement."""
    import time

    from netmeter.database import connect, get_networks, init_db, save_measurement

    init_db()

    for name in ["OldNet", "NewNet"]:
        save_measurement(
            {"network_name": name, "network_type": "wifi", "interface": "wlan0"},
            {
                "download_mbps": 50.0,
                "upload_mbps": 10.0,
                "ping_ms": 20.0,
                "server_name": "",
                "server_country": "",
                "raw_json": "{}",
            },
        )
        time.sleep(0.01)

    with connect() as conn:
        networks = get_networks(conn)

    assert networks[0] == "NewNet"
