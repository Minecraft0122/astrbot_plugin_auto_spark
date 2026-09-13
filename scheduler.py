"""Per-session scheduler for AstrBot auto spark plugin."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Awaitable, Callable


class SparkScheduler:
    def __init__(self, send: Callable[[str, str], Awaitable[bool]], interval: int, message: str, send_on_startup: bool = False, send_times: list[str] | None = None):
        self._send = send
        self.interval = max(10, int(interval))
        self.message = message
        self.send_on_startup = send_on_startup
        self.send_times = self._normalize_times(send_times or [])
        self._tasks: dict[str, asyncio.Task] = {}
        self._stopping = False

    @staticmethod
    def _normalize_times(values: list[str]) -> list[str]:
        result = set()
        for value in values:
            try:
                hour, minute = str(value).strip().split(":", 1)
                hour, minute = int(hour), int(minute)
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    result.add(f"{hour:02d}:{minute:02d}")
            except (TypeError, ValueError):
                continue
        return sorted(result)

    @property
    def targets(self) -> tuple[str, ...]:
        return tuple(self._tasks)

    def start(self, umo: str) -> bool:
        if self._stopping or not umo or umo in self._tasks:
            return False
        self._tasks[umo] = asyncio.create_task(self._run(umo), name=f"auto_spark:{umo}")
        return True

    async def stop(self, umo: str) -> bool:
        task = self._tasks.pop(umo, None)
        if task is None:
            return False
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return True

    def _delay_to_next_time(self) -> float:
        now = datetime.now()
        candidates = []
        for value in self.send_times:
            hour, minute = map(int, value.split(":"))
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            candidates.append(candidate)
        return max(1.0, (min(candidates) - now).total_seconds())

    async def _run(self, umo: str):
        first = True
        try:
            while not self._stopping:
                if first and self.send_on_startup:
                    await self._safe_send(umo)
                first = False
                if self.send_times:
                    await asyncio.sleep(self._delay_to_next_time())
                else:
                    await asyncio.sleep(self.interval)
                if not self._stopping:
                    await self._safe_send(umo)
        except asyncio.CancelledError:
            raise

    async def _safe_send(self, umo: str) -> None:
        try:
            await self._send(umo, self.message)
        except Exception:
            # A failed send must not kill scheduling for this target.
            pass

    async def stop_all(self):
        self._stopping = True
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
