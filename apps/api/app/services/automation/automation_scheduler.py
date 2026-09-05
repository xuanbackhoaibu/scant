import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import zoneinfo
from croniter import croniter
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.entities import Automation
from app.repositories.base import BaseRepository

logger = logging.getLogger("automation.scheduler")


class AutomationScheduler:
    """
    Real Report Automation Scheduler.
    Manages cron schedules, timezones, next_run_at calculations,
    and a reliable background worker loop with concurrency protection.
    """

    DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"

    def __init__(self):
        self._loop_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._active_locks: set[str] = set()
        self._poll_interval_seconds: int = 15

    @classmethod
    def get_zoneinfo(cls, tz_name: Optional[str]) -> zoneinfo.ZoneInfo:
        if not tz_name:
            tz_name = cls.DEFAULT_TIMEZONE
        try:
            return zoneinfo.ZoneInfo(tz_name.strip())
        except Exception:
            try:
                return zoneinfo.ZoneInfo(cls.DEFAULT_TIMEZONE)
            except Exception:
                return zoneinfo.ZoneInfo("UTC")

    @classmethod
    def compute_next_run(
        cls,
        trigger_type: str,
        cron_expression: Optional[str],
        tz_name: Optional[str] = None,
        base_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Calculates the next run datetime in UTC.
        Supports standard cron expressions ('0 8 * * *', '*/15 * * * *'),
        convenience aliases ('@daily', '@weekly', '@monthly', '@hourly'),
        and intervals ('interval:30m', 'interval:2h', 'interval:1d').
        """
        if trigger_type != "schedule" or not cron_expression:
            return None

        tz = cls.get_zoneinfo(tz_name)
        now_in_tz = (base_time or datetime.now(timezone.utc)).astimezone(tz)
        raw_expr = cron_expression.strip().lower()

        # 1. Handle interval patterns: interval:15m, interval:2h, interval:1d
        interval_match = re.match(r"^interval:(\d+)([smhd])$", raw_expr)
        if interval_match:
            val = int(interval_match.group(1))
            unit = interval_match.group(2)
            delta = timedelta(
                seconds=val if unit == "s" else 0,
                minutes=val if unit == "m" else 0,
                hours=val if unit == "h" else 0,
                days=val if unit == "d" else 0,
            )
            next_local = now_in_tz + delta
            return next_local.astimezone(timezone.utc)

        # 2. Normalize aliases
        alias_map = {
            "@daily": "0 8 * * *",
            "daily": "0 8 * * *",
            "@hourly": "0 * * * *",
            "hourly": "0 * * * *",
            "@weekly": "0 8 * * 1",
            "weekly": "0 8 * * 1",
            "@monthly": "0 8 1 * *",
            "monthly": "0 8 1 * *",
        }
        cron_str = alias_map.get(raw_expr, cron_expression.strip())

        try:
            itr = croniter(cron_str, now_in_tz)
            next_local = itr.get_next(datetime)
            # Ensure next_local is timezone-aware in target tz
            if next_local.tzinfo is None:
                next_local = next_local.replace(tzinfo=tz)
            return next_local.astimezone(timezone.utc)
        except Exception as e:
            logger.warning(f"Failed to calculate next_run for cron '{cron_expression}': {e}")
            return None

    async def recalibrate_active_schedules(self):
        """Called on startup: recalibrates next_run_at for all active scheduled automations."""
        async with AsyncSessionLocal() as db:
            try:
                now_utc = datetime.now(timezone.utc)
                stmt = select(Automation).where(
                    and_(
                        Automation.is_active == True,
                        Automation.trigger_type == "schedule",
                    )
                )
                res = await db.execute(stmt)
                automations = res.scalars().all()
                auto_repo = BaseRepository[Automation](Automation)

                updated_count = 0
                for auto in automations:
                    if not auto.next_run_at or auto.next_run_at <= now_utc:
                        next_run = self.compute_next_run(
                            trigger_type=auto.trigger_type,
                            cron_expression=auto.cron_expression,
                            tz_name=auto.timezone,
                            base_time=now_utc,
                        )
                        if next_run:
                            await auto_repo.update(db, db_obj=auto, obj_in={"next_run_at": next_run})
                            updated_count += 1
                await db.commit()
                logger.info(f"Recalibrated {updated_count} active scheduled automations on startup.")
            except Exception as ex:
                logger.error(f"Error during recalibrate_active_schedules: {ex}", exc_info=True)

    async def _execute_due_automation(self, automation_id: str):
        """Safely executes an automation with locking to prevent overlapping runs."""
        if automation_id in self._active_locks:
            logger.warning(f"Automation {automation_id} is already executing, skipping duplicate trigger.")
            return

        self._active_locks.add(automation_id)
        try:
            from app.services.automation.automation_engine import automation_engine
            async with AsyncSessionLocal() as db:
                await automation_engine.execute_run(db, automation_id, trigger_source="schedule")
                await db.commit()
        except Exception as ex:
            logger.error(f"Error executing scheduled automation {automation_id}: {ex}", exc_info=True)
        finally:
            self._active_locks.discard(automation_id)

    async def _scheduler_loop(self):
        """Continuous background loop checking due automations."""
        logger.info("Report Automation Scheduler loop started.")
        while self._is_running:
            try:
                now_utc = datetime.now(timezone.utc)
                async with AsyncSessionLocal() as db:
                    stmt = select(Automation).where(
                        and_(
                            Automation.is_active == True,
                            Automation.trigger_type == "schedule",
                            Automation.next_run_at != None,
                            Automation.next_run_at <= now_utc,
                        )
                    )
                    res = await db.execute(stmt)
                    due_automations = res.scalars().all()
                    auto_repo = BaseRepository[Automation](Automation)

                    for auto in due_automations:
                        # Advance next_run_at immediately so subsequent loop ticks don't re-pick it up
                        subsequent_run = self.compute_next_run(
                            trigger_type=auto.trigger_type,
                            cron_expression=auto.cron_expression,
                            tz_name=auto.timezone,
                            base_time=now_utc,
                        )
                        await auto_repo.update(db, db_obj=auto, obj_in={"next_run_at": subsequent_run})
                        await db.commit()

                        # Dispatch run in background task
                        asyncio.create_task(self._execute_due_automation(auto.id))

            except asyncio.CancelledError:
                break
            except Exception as ex:
                logger.error(f"Scheduler loop error: {ex}", exc_info=True)

            await asyncio.sleep(self._poll_interval_seconds)

        logger.info("Report Automation Scheduler loop stopped.")

    def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())

    def stop(self):
        self._is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()


automation_scheduler = AutomationScheduler()
