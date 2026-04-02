"""Run a speed test and return structured results."""

import json
import logging

import speedtest

log = logging.getLogger("netmeter")


def run_speedtest() -> dict:
    """Execute a speed test and return download/upload/ping results."""
    log.info("Starting speed test...")
    st = speedtest.Speedtest()
    st.get_best_server()
    st.download()
    st.upload()
    results = st.results.dict()

    download_mbps = results["download"] / 1_000_000
    upload_mbps = results["upload"] / 1_000_000
    ping_ms = results["ping"]
    server = results.get("server", {})

    log.info(
        "Results: %.1f Mbps down, %.1f Mbps up, %.1f ms ping",
        download_mbps,
        upload_mbps,
        ping_ms,
    )

    return {
        "download_mbps": round(download_mbps, 2),
        "upload_mbps": round(upload_mbps, 2),
        "ping_ms": round(ping_ms, 2),
        "server_name": server.get("sponsor", ""),
        "server_country": server.get("country", ""),
        "raw_json": json.dumps(results),
    }
