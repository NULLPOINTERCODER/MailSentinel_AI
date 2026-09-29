import pytest
from app.workers.celery_app import celery_app
from app.workers.tasks import run_async


def test_celery_app_configuration():
    """Test Celery configuration, beat schedule, and registered tasks."""
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.task_serializer == "json"
    assert "periodic-sync-all-users-inbox" in celery_app.conf.beat_schedule
    assert (
        celery_app.conf.beat_schedule["periodic-sync-all-users-inbox"]["task"]
        == "app.workers.tasks.sync_all_active_users_task"
    )


def test_run_async_utility():
    """Verify run_async utility can execute async coroutine synchronously."""
    async def sample_coroutine():
        return "async_success"

    result = run_async(sample_coroutine())
    assert result == "async_success"
