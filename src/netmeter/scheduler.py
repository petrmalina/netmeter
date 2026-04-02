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


_PLACEHOLDER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>NetMeter</title>
<style>
  body { background: #1a1a2e; color: #e0e0e0; font-family: system-ui, sans-serif;
         display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
  .card { text-align: center; padding: 3rem; }
  h1 { font-size: 2rem; margin-bottom: 0.5rem; }
  p { color: #888; font-size: 1.1rem; }
  .spinner { display: inline-block; width: 24px; height: 24px; border: 3px solid #444;
             border-top-color: #6c63ff; border-radius: 50%; animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="card">
  <h1>NetMeter</h1>
  <p><span class="spinner"></span></p>
  <p>Waiting for the first measurement&hellip;</p>
  <p>This page will refresh automatically.</p>
</div>
</body>
</html>
"""


class _DashboardHandler(SimpleHTTPRequestHandler):
    """Serves dashboard.html, falling back to a placeholder if it doesn't exist yet."""

    def do_GET(self) -> None:
        dashboard = OUTPUT_DIR / "dashboard.html"
        if self.path in ("/", "/index.html") and not dashboard.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_PLACEHOLDER_HTML.encode())
            return
        if self.path == "/":
            self.path = "/dashboard.html"
        super().do_GET()

    def log_message(self, fmt: str, *args: object) -> None:
        return


def _start_dashboard_server() -> HTTPServer | None:
    """Start a background HTTP server for the dashboard if a port is configured."""
    if DASHBOARD_PORT <= 0:
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(_DashboardHandler, directory=str(OUTPUT_DIR))
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
