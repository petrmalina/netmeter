"""Command-line entry points for NetMeter."""

import logging
import sys
import time

import speedtest

from netmeter.config import LOG_LEVEL, MEASURE_RETRIES, MEASURE_RETRY_DELAY
from netmeter.dashboard import generate_dashboard
from netmeter.database import init_db, save_measurement
from netmeter.measure import run_speedtest
from netmeter.network import get_network_info

log = logging.getLogger("netmeter")


def setup_logging() -> None:
    """Configure root logger with structured format."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def measure_once() -> None:
    """Run a single measurement cycle: detect network, test, save, regenerate dashboard."""
    setup_logging()
    init_db()

    network_info = get_network_info()
    log.info(
        "Network: %s (%s, %s)",
        network_info["network_name"],
        network_info["network_type"],
        network_info["interface"],
    )

    if network_info["network_name"] == "unknown":
        log.warning("No active network connection detected. Skipping measurement.")
        return

    for attempt in range(1, MEASURE_RETRIES + 1):
        try:
            speed_data = run_speedtest()
            save_measurement(network_info, speed_data)
            generate_dashboard()
            return
        except speedtest.SpeedtestException as e:
            log.warning("Attempt %d/%d failed: %s", attempt, MEASURE_RETRIES, e)
            if attempt < MEASURE_RETRIES:
                time.sleep(MEASURE_RETRY_DELAY)
            else:
                log.error("Speed test failed after %d attempts.", MEASURE_RETRIES)
                sys.exit(1)


def run_dashboard() -> None:
    """Regenerate the dashboard from existing data."""
    setup_logging()
    generate_dashboard()


def main() -> None:
    """Entry point dispatcher."""
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        run_dashboard()
    else:
        measure_once()
