# packages/core/src/zorivest_core/services/scheduler_service.py
"""APScheduler wrapper for policy scheduling (Phase 9, §9.3d).

Manages scheduler lifecycle, job CRUD, and cron-based policy execution.

Spec: 09-scheduling.md §9.3d
MEU: MEU-89 (scheduling-api-mcp)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

import structlog


logger = structlog.get_logger()

# Module-level singleton reference for the APScheduler job callback.
# APScheduler pickles job functions; bound methods pickle `self`, which
# transitively holds the SQLAlchemy Engine (unpicklable in SA 2.x).
# This global lets us use a picklable module-level function instead.
_scheduler_instance: SchedulerService | None = None


async def _execute_policy_callback(policy_id: str) -> None:
    """Module-level APScheduler job callback (picklable).

    Delegates to the global SchedulerService instance. This function
    is registered with APScheduler instead of a bound method to avoid
    pickling the SchedulerService (which holds pipeline_runner → uow → engine).
    """
    if _scheduler_instance is None:
        logger.error("scheduler_callback_no_instance", policy_id=policy_id)
        return
    await _scheduler_instance._execute_policy(policy_id)


class PipelineRunnerPort(Protocol):
    """Minimal interface for the pipeline runner used by scheduler callbacks."""

    async def run(
        self,
        policy: Any,
        trigger_type: str,
        dry_run: bool = False,
        resume_from: str | None = None,
        actor: str = "",
        policy_id: str = "",
    ) -> Any: ...


class PolicyRepositoryPort(Protocol):
    """Minimal policy repo port for scheduler callbacks."""

    async def get_by_id(self, policy_id: str) -> Any: ...


class SchedulerService:
    """Manages APScheduler lifecycle and policy scheduling.

    The scheduler uses the same SQLCipher database as the application
    (via SQLAlchemyJobStore) to persist job state across restarts.
    """

    def __init__(
        self,
        pipeline_runner: PipelineRunnerPort | None = None,
        policy_repo: PolicyRepositoryPort | None = None,
        db_url: str | None = None,
    ) -> None:
        global _scheduler_instance
        self.pipeline_runner = pipeline_runner
        self.policy_repo = policy_repo
        self._running = False
        self._jobs: dict[str, dict[str, Any]] = {}
        self._scheduler: Any = None
        _scheduler_instance = self  # Register for module-level callback

        # Lazy APScheduler init — only if db_url provided
        if db_url:
            try:
                from apscheduler.schedulers.asyncio import AsyncIOScheduler
                from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

                self._scheduler = AsyncIOScheduler(
                    jobstores={"default": SQLAlchemyJobStore(url=db_url)},
                    job_defaults={
                        "coalesce": True,
                        "max_instances": 1,
                        "misfire_grace_time": 3600,
                    },
                )
            except ImportError:
                logger.warning("apscheduler_not_available")

    @property
    def scheduler(self) -> Any:
        """Access underlying APScheduler instance."""
        return self._scheduler

    async def start(self) -> None:
        """Start the scheduler (call during FastAPI lifespan startup)."""
        if self._scheduler:
            self._scheduler.start()
        self._running = True
        logger.info("scheduler_started", job_count=len(self._jobs))

    async def shutdown(self) -> None:
        """Graceful shutdown (call during FastAPI lifespan shutdown)."""
        if self._scheduler:
            self._scheduler.shutdown(wait=True)
        self._running = False
        logger.info("scheduler_shutdown")

    def schedule_policy(
        self,
        policy_name: str,
        policy_id: str,
        cron_expression: str,
        timezone: str = "UTC",
        coalesce: bool = True,
        max_instances: int = 1,
        misfire_grace_time: int = 3600,
    ) -> None:
        """Add or update a scheduled job for a policy."""
        job_id = f"policy_{policy_id}"
        self._jobs[job_id] = {
            "id": job_id,
            "name": policy_name,
            "policy_id": policy_id,
            "cron": cron_expression,
            "timezone": timezone,
            "next_run": None,
        }

        if self._scheduler:
            from apscheduler.triggers.cron import CronTrigger

            parts = cron_expression.split()
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone=timezone,
            )
            # Use module-level function ref (picklable) instead of bound method.
            # APScheduler resolves the "module:function" string at call time.
            self._scheduler.add_job(
                func=f"{__name__}:_execute_policy_callback",
                trigger=trigger,
                id=job_id,
                name=policy_name,
                args=[policy_id],
                replace_existing=True,
                coalesce=coalesce,
                max_instances=max_instances,
                misfire_grace_time=misfire_grace_time,
            )

        logger.info("policy_scheduled", policy=policy_name, cron=cron_expression)

    def unschedule_policy(self, policy_id: str) -> None:
        """Remove a policy's scheduled job."""
        job_id = f"policy_{policy_id}"
        self._jobs.pop(job_id, None)
        if self._scheduler:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass

    def get_next_run(self, policy_id: str) -> datetime | None:
        """Get the next fire time for a policy's job."""
        job_id = f"policy_{policy_id}"
        if self._scheduler:
            job = self._scheduler.get_job(job_id)
            return job.next_run_time if job else None
        return None

    def pause_policy(self, policy_id: str) -> None:
        """Pause a policy's scheduled job."""
        if self._scheduler:
            self._scheduler.pause_job(f"policy_{policy_id}")

    def resume_policy(self, policy_id: str) -> None:
        """Resume a policy's scheduled job."""
        if self._scheduler:
            self._scheduler.resume_job(f"policy_{policy_id}")

    def get_status(self) -> dict[str, Any]:
        """Return scheduler status for diagnostics."""
        if self._scheduler:
            jobs = self._scheduler.get_jobs()
            return {
                "running": self._scheduler.running,
                "job_count": len(jobs),
                "jobs": [
                    {
                        "id": j.id,
                        "name": j.name,
                        "next_run": (
                            j.next_run_time.isoformat() if j.next_run_time else None
                        ),
                    }
                    for j in jobs
                ],
            }
        return {
            "running": self._running,
            "job_count": len(self._jobs),
            "jobs": list(self._jobs.values()),
        }

    async def _execute_policy(self, policy_id: str) -> None:
        """Job callback: load policy from DB, deserialize, and execute."""
        if not self.pipeline_runner or not self.policy_repo:
            logger.error("scheduler_missing_deps", policy_id=policy_id)
            return
        policy = await self.policy_repo.get_by_id(policy_id)
        if not policy:
            logger.warning("scheduled_policy_not_found", policy_id=policy_id)
            return

        # Deserialize: repo returns dict/model with policy_json field
        policy_json = (
            policy.get("policy_json", policy)
            if isinstance(policy, dict)
            else getattr(policy, "policy_json", policy)
        )
        from zorivest_core.domain.pipeline import PolicyDocument

        doc = (
            PolicyDocument(**policy_json)
            if isinstance(policy_json, dict)
            else policy_json
        )

        await self.pipeline_runner.run(
            policy=doc,
            trigger_type="scheduled",
            policy_id=policy_id,
        )
