import asyncio
import logging
from app.workers.tasks import _async_sync_all_active_users

logger = logging.getLogger(__name__)


class DevBackgroundScheduler:
    """Lightweight in-process async scheduler for local development.
    
    Runs periodic inbox synchronization and AI triage in the background
    without strictly requiring a live Celery daemon / Redis service.
    """

    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._is_running = False

    async def _loop(self):
        logger.info("DevBackgroundScheduler started. Running sync every %d seconds.", self.interval_seconds)
        while self._is_running:
            try:
                await asyncio.sleep(self.interval_seconds)
                logger.info("DevBackgroundScheduler triggering scheduled inbox synchronization...")
                result = await _async_sync_all_active_users()
                logger.info("DevBackgroundScheduler periodic sync finished: %s", result)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in DevBackgroundScheduler loop: %s", e)

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        if self._is_running and self._task:
            self._is_running = False
            self._task.cancel()
            logger.info("DevBackgroundScheduler stopped.")
