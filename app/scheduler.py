"""Scheduler diario para sincronizar com o Converts.

Usa APScheduler em modo background. No Render free tier o web service
fica suspenso quando ocioso, entao para garantir execucao garantida
recomenda-se um Cron Job separado (ver README, secao 'Render Cron Job').
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
_scheduler = None


def init_scheduler(app):
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    tz = app.config.get("TZ", "America/Sao_Paulo")
    hour = int(app.config.get("SYNC_HOUR", 23))
    minute = int(app.config.get("SYNC_MINUTE", 30))

    _scheduler = BackgroundScheduler(timezone=tz)

    def job():
        with app.app_context():
            from .converts.sync_service import run_sync
            try:
                log = run_sync(triggered_by="scheduler")
                logger.info("Sync diario ok status=%s novos=%s dup=%s", log.status, log.inserted, log.duplicates)
            except Exception as exc:
                logger.exception("Falha sync diario: %s", exc)

    _scheduler.add_job(
        job,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="converts_daily_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler iniciado: sync diario %02d:%02d (%s)", hour, minute, tz)
    return _scheduler
