"""Per-session scheduler for AstrBot auto spark plugin."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable

@dataclass(frozen=True)
class SparkTarget:
    """A target UMO: platform instance id, message type and session id."""
    umo: str

class SparkScheduler:
    def __init__(self, send: Callable[[str, str], Awaitable[bool]], interval: int, message: str, send_on_startup: bool = False):
        self._send, self.interval, self.message, self.send_on_startup = send, max(10, int(interval)), message, send_on_startup
        self._tasks: dict[str, asyncio.Task] = {}
        self._stopping = False

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

    async def _run(self, umo: str):
        first = True
        try:
            while not self._stopping:
                if self.send_on_startup or not first:
                    try:
                        await self._send(umo, self.message)
                    except Exception:
                        # A failed send must not kill scheduling for this target.
                        pass
                first = False
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            raise

    async def stop_all(self):
        self._stopping = True
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
