import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import get_settings
from db.session import SessionLocal
from scheduler.jobs import poll_all_products

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_poll_job() -> None:
    db = SessionLocal()
    try:
        count = poll_all_products(db)
        logger.info("Poll job completed for %s active product(s)", count)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        logger.info("Scheduler already running; skipping duplicate start")
        return _scheduler

    settings = get_settings()
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_poll_job,
        trigger=IntervalTrigger(seconds=settings.poll_interval_seconds),
        id="poll_products",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started; polling every %s seconds", settings.poll_interval_seconds
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
