"""Once-per-day scheduler for AstrBot auto spark."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Awaitable, Callable


class SparkScheduler:
    def __init__(self, send_group: Callable[[str, str], Awaitable[bool]], send_private: Callable[[str, str], Awaitable[bool]], message: str, send_time: str = "09:00", send_on_startup: bool = False, target_provider: Callable[[], tuple[list[str], list[str]]] | None = None):
        self._send_group = send_group
        self._send_private = send_private
        self.message = message
        self.send_time = self._normalize_time(send_time) or "09:00"
        self.send_on_startup = send_on_startup
        self._target_provider = target_provider
        self._task: asyncio.Task | None = None
        self._stopping = False
        self._last_sent_date: str | None = None

    @staticmethod
    def _normalize_time(value: str) -> str | None:
        try:
            hour, minute = map(int, str(value).strip().split(":", 1))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        except (TypeError, ValueError):
            return None
        return None

    def start(self) -> bool:
        if self._task is not None:
            return False
        self._stopping = False
        self._task = asyncio.create_task(self._run(), name="auto_spark:daily")
        return True

    def _delay_to_next_time(self) -> float:
        now = datetime.now()
        hour, minute = map(int, self.send_time.split(":"))
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return max(0.5, (candidate - now).total_seconds())

    async def _run(self) -> None:
        if self.send_on_startup:
            await self.send_once()
        try:
            while not self._stopping:
                await asyncio.sleep(self._delay_to_next_time())
                if not self._stopping:
                    await self.send_once()
        except asyncio.CancelledError:
            raise

    async def send_once(self, group_targets: list[str] | None = None, private_targets: list[str] | None = None) -> tuple[int, int]:
        """Send once to each group and private target; return (group_success, private_success)."""
        if group_targets is None or private_targets is None:
            group_targets, private_targets = self._target_provider() if self._target_provider else ([], [])
        groups = group_targets
        privates = private_targets
        group_ok = private_ok = 0
        for target in groups:
            try:
                if await self._send_group(target, self.message):
                    group_ok += 1
            except Exception:
                pass
        for target in privates:
            try:
                if await self._send_private(target, self.message):
                    private_ok += 1
            except Exception:
                pass
        self._last_sent_date = datetime.now().date().isoformat()
        return group_ok, private_ok

    async def stop(self) -> None:
        self._stopping = True
        if self._task is not None:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
