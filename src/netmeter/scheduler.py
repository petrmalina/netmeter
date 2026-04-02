"""Built-in scheduler for running measurements at a fixed interval.

Optionally serves the dashboard over HTTP when NETMETER_DASHBOARD_PORT is set.
Used by Docker and service installers instead of cron.
"""

import functools
import logging
import signal
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

from netmeter.cli import measure_once, setup_logging
from netmeter.config import DASHBOARD_HOST, DASHBOARD_PORT, MEASURE_INTERVAL_SECONDS, OUTPUT_DIR

log = logging.getLogger("netmeter")

_running = True


def _handle_signal(signum: int, _frame: object) -> None:
    global _running
    log.info("Received signal %d, shutting down gracefully...", signum)
    _running = False


def _start_dashboard_server() -> HTTPServer | None:
    """Start a background HTTP server for the dashboard if a port is configured."""
    if DASHBOARD_PORT <= 0:
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(OUTPUT_DIR))
    server = HTTPServer((DASHBOARD_HOST, DASHBOARD_PORT), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("Dashboard server started on http://%s:%d", DASHBOARD_HOST, DASHBOARD_PORT)
    return server


def run_scheduler() -> None:
    """Run measurements in a loop at the configured interval."""
    setup_logging()
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    server = _start_dashboard_server()
    log.info("Scheduler started. Interval: %ds", MEASURE_INTERVAL_SECONDS)

    while _running:
        try:
            measure_once()
        except SystemExit:
            pass
        except Exception:
            log.exception("Unexpected error during measurement")

        deadline = time.monotonic() + MEASURE_INTERVAL_SECONDS
        while _running and time.monotonic() < deadline:
            time.sleep(1)

    if server:
        server.shutdown()
    log.info("Scheduler stopped.")
    sys.exit(0)
