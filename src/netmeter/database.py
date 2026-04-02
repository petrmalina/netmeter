"""SQLite database initialization and data access."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from netmeter.config import DB_DIR, DB_PATH


def init_db() -> None:
    """Create the database directory and schema if they don't exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                network_name TEXT NOT NULL,
                network_type TEXT NOT NULL,
                interface TEXT NOT NULL,
                download_mbps REAL NOT NULL,
                upload_mbps REAL NOT NULL,
                ping_ms REAL NOT NULL,
                server_name TEXT,
                server_country TEXT,
                raw_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_measurements_network
            ON measurements(network_name, timestamp)
        """)
        conn.commit()


@contextmanager
def connect():
    """Yield a database connection that is always closed properly."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        yield conn
    finally:
        conn.close()


def save_measurement(network_info: dict, speed_data: dict) -> None:
    """Insert a single measurement row into the database."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO measurements
                (timestamp, network_name, network_type, interface,
                 download_mbps, upload_mbps, ping_ms,
                 server_name, server_country, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                network_info["network_name"],
                network_info["network_type"],
                network_info["interface"],
                speed_data["download_mbps"],
                speed_data["upload_mbps"],
                speed_data["ping_ms"],
                speed_data["server_name"],
                speed_data["server_country"],
                speed_data["raw_json"],
            ),
        )
        conn.commit()


def get_networks(conn) -> list[str]:
    """Return network names ordered by most recent measurement."""
    rows = conn.execute(
        "SELECT network_name FROM measurements GROUP BY network_name ORDER BY MAX(timestamp) DESC"
    ).fetchall()
    return [r[0] for r in rows]


def get_network_stats(conn, network_name: str) -> dict:
    """Return aggregate statistics for a single network."""
    row = conn.execute(
        """
        SELECT
            AVG(download_mbps), AVG(upload_mbps), AVG(ping_ms),
            COUNT(*), MAX(timestamp), network_type
        FROM measurements
        WHERE network_name = ?
        """,
        (network_name,),
    ).fetchone()
    last_ts = row[4]
    try:
        dt = datetime.fromisoformat(last_ts)
        last_measured = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        last_measured = last_ts or "—"
    return {
        "avg_download": row[0] or 0,
        "avg_upload": row[1] or 0,
        "avg_ping": row[2] or 0,
        "measurement_count": row[3],
        "last_measured": last_measured,
        "type": row[5] or "unknown",
    }


def fetch_data(conn, network_name: str, hours: int, aggregate: str | None) -> dict:
    """Fetch time-series data for graphing, optionally aggregated."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    if aggregate == "hour":
        query = """
            SELECT strftime('%Y-%m-%dT%H:00:00', timestamp) as ts,
                   AVG(download_mbps), AVG(upload_mbps), AVG(ping_ms)
            FROM measurements WHERE network_name = ? AND timestamp >= ?
            GROUP BY ts ORDER BY ts
        """
    elif aggregate == "day":
        query = """
            SELECT strftime('%Y-%m-%dT00:00:00', timestamp) as ts,
                   AVG(download_mbps), AVG(upload_mbps), AVG(ping_ms)
            FROM measurements WHERE network_name = ? AND timestamp >= ?
            GROUP BY ts ORDER BY ts
        """
    else:
        query = """
            SELECT timestamp, download_mbps, upload_mbps, ping_ms
            FROM measurements WHERE network_name = ? AND timestamp >= ?
            ORDER BY timestamp
        """

    rows = conn.execute(query, (network_name, since)).fetchall()

    timestamps, downloads, uploads, pings = [], [], [], []
    for row in rows:
        try:
            ts = datetime.fromisoformat(row[0])
        except (ValueError, TypeError):
            continue
        timestamps.append(ts)
        downloads.append(row[1])
        uploads.append(row[2])
        pings.append(row[3])

    return {
        "timestamps": timestamps,
        "downloads": downloads,
        "uploads": uploads,
        "pings": pings,
    }
