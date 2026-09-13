from __future__ import annotations

from typing import Any

from astrbot import logger
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star, register
from astrbot.core.platform.message_session import MessageSession
from astrbot.core.platform.message_type import MessageType

try:
    from astrbot.core.config.astrbot_config import AstrBotConfig
except ImportError:
    AstrBotConfig = dict  # type: ignore

try:
    from .scheduler import SparkScheduler
except ImportError:  # pragma: no cover
    from scheduler import SparkScheduler


@register("auto_spark", "AstrBot", "每天向多个群聊和私聊发送一次续火消息", "2.2.0")
class AutoSparkPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        cfg = config or {}
        self.message = str(cfg.get("message", "续火啦 🔥"))
        self.enabled = bool(cfg.get("enabled", True))
        self.platform_ids = self._parse_platform_ids(cfg.get("platform_ids", cfg.get("platform_id", "")))
        self.send_time = self._parse_time(cfg.get("send_time", "09:00")) or "09:00"
        self.group_targets = self._parse_targets(cfg.get("group_targets", []), MessageType.GROUP_MESSAGE)
        self.private_targets = self._parse_targets(cfg.get("private_targets", []), MessageType.FRIEND_MESSAGE)
        self.scheduler = SparkScheduler(
            self._send_group,
            self._send_private,
            self.message,
            self.send_time,
            target_provider=lambda: (self.group_targets, self.private_targets),
        )

    @staticmethod
    def _parse_time(raw: Any) -> str | None:
        try:
            hour, minute = map(int, str(raw).strip().split(":", 1))
        except (TypeError, ValueError):
            return None
        return f"{hour:02d}:{minute:02d}" if 0 <= hour <= 23 and 0 <= minute <= 59 else None

    @staticmethod
    def _parse_platform_ids(raw: Any) -> list[str]:
        values = raw if isinstance(raw, (list, tuple, set)) else str(raw or "").replace("，", "\n").replace(",", "\n").splitlines()
        return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))

    def _parse_targets(self, raw: Any, expected_type: MessageType) -> list[str]:
        values = raw if isinstance(raw, (list, tuple, set)) else str(raw or "").replace("，", "\n").replace(",", "\n").splitlines()
        result: list[str] = []
        for value in values:
            value = str(value).strip()
            if not value:
                continue
            # A bare group/user ID is expanded to every configured bot instance.
            if ":" not in value:
                if not self.platform_ids:
                    logger.warning(
                        "auto_spark: target %r requires platform_ids; "
                        "fill platform_ids with one or more bot instance IDs, "
                        "or use a complete UMO",
                        value,
                    )
                    continue
                umos = [str(MessageSession(platform_id, expected_type, value)) for platform_id in self.platform_ids]
            else:
                umos = [value]
            for umo in umos:
                try:
                    session = MessageSession.from_str(umo)
                    if session.message_type != expected_type:
                        raise ValueError("wrong message type")
                except Exception:
                    logger.warning("auto_spark: ignore invalid %s target %r", expected_type.value, umo)
                    continue
                if umo not in result:
                    result.append(umo)
        return result

    async def initialize(self):
        if self.enabled and (self.group_targets or self.private_targets):
            self.scheduler.start()

    async def _send_group(self, umo: str, text: str) -> bool:
        return bool(await self.context.send_message(umo, MessageChain([Plain(text)])))

    async def _send_private(self, umo: str, text: str) -> bool:
        return bool(await self.context.send_message(umo, MessageChain([Plain(text)])))

    async def terminate(self):
        await self.scheduler.stop()
