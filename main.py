import logging

from logging_config import setup_logging

setup_logging()

from jobs.score_messages import run_evaluate_job
from jobs.fetch_messages import run_fetch_job
from jobs.forward_matches import run_forward_job
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from config import settings
from services.bot_handler import build_bot_app

logger = logging.getLogger(__name__)


def _on_job_event(event):
    """Logs a scheduled job's success/failure after each run."""
    if event.exception:
        logger.error("[scheduler] job '%s' raised an exception: %s", event.job_id, event.exception)
    else:
        logger.info("[scheduler] job '%s' finished", event.job_id)


async def main():
    logger.info("Starting job_matcher service")

    bot_app = build_bot_app()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    logger.info("Telegram bot polling started")

    scheduler = AsyncIOScheduler()

    scheduler.add_job(run_fetch_job, "interval", minutes=settings.fetch_interval_minutes, id="fetch")
    scheduler.add_job(run_evaluate_job, "interval", minutes=settings.evaluate_interval_minutes, id="evaluate")
    scheduler.add_job(run_forward_job, "interval", minutes=settings.forward_interval_minutes, id="forward")

    scheduler.add_listener(_on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.start()
    logger.info(
        "Scheduler started (fetch=%dmin, evaluate=%dmin, forward=%dmin)",
        settings.fetch_interval_minutes,
        settings.evaluate_interval_minutes,
        settings.forward_interval_minutes,
    )

    logger.info("Running fetch, evaluate, forward once on startup")
    await asyncio.gather(run_fetch_job(), run_evaluate_job(), run_forward_job())

    logger.info("Startup jobs complete — service is now running on schedule")
    await asyncio.Event().wait()  # keep alive


if __name__ == "__main__":
    asyncio.run(main())
