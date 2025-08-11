import logging
import subprocess

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

log = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone=timezone("Asia/Kolkata"))


def start_scheduler():
    # Run every night at 02:30 IST
    scheduler.add_job(run_ai_populator, CronTrigger(hour=2, minute=30))
    scheduler.start()
    log.info("Nightly AI insights job scheduled for 02:30 IST.")


def run_ai_populator():
    log.info("Starting nightly AI insights populator...")
    try:
        result = subprocess.run(
            ["python3", "scripts/ai_insights_populator.py"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log.info("AI insights populator finished successfully:\n%s", result.stdout)
        else:
            log.error("AI insights populator failed:\n%s", result.stderr)
    except Exception as e:
        log.exception("Error running AI insights populator: %s", e)


def shutdown_scheduler():
    scheduler.shutdown()
