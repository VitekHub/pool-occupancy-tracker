"""Scheduler for Pool Occupancy Tracker — runs occupancy + aggregation
every 10 minutes during operating hours (6–22 Prague time, first run 6:10)
and capacity analysis once daily at 4:00 AM Prague time.

Intended for Docker deployments.  For scheduled CI runs, see
.github/workflows/schedule.yml.
"""

import logging
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import schedule

PRAGUE = ZoneInfo("Europe/Prague")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run(cmd: str) -> None:
    """Run a shell command and log the result."""
    logger.info("Running: %s", cmd)
    result = subprocess.run(cmd, shell=True)  # noqa: S602
    if result.returncode != 0:
        logger.error("Command failed: %s (exit %d)", cmd, result.returncode)


def _is_operating_hours(now: datetime) -> bool:
    """Return True if *now* is within operating hours (6–22 Prague time).

    Boundaries are excluded: first run at 6:10, last run at 21:50.
    """
    hour, minute = now.hour, now.minute
    if hour < 6 or hour >= 22:
        return False
    # First 10 minutes of the opening hour are excluded
    if hour == 6 and minute < 10:
        return False
    return True


def run_occupancy() -> None:
    """Run occupancy tracker + aggregation if within operating hours."""
    now = datetime.now(PRAGUE)
    if not _is_operating_hours(now):
        logger.info("Outside operating hours (%s), skipping", now.strftime("%H:%M"))
        return
    run("python occupancy.py")
    run("python -m pool_aggregation")


def run_capacity() -> None:
    """Run capacity tracker."""
    run("python capacity.py")


# ── Schedule ──────────────────────────────────────────────────────────
schedule.every(10).minutes.do(run_occupancy)
schedule.every().day.at("04:00").do(run_capacity)

# Run occupancy immediately on startup (if within operating hours)
run_occupancy()

logger.info("Scheduler started — occupancy every 10 min (6–22, first run 6:10), capacity daily at 04:00")

while True:
    schedule.run_pending()
    time.sleep(1)