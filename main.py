from __future__ import annotations
import asyncio, json
from pathlib import Path
from typing import Any
from astrbot import logger
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain
try:
    from astrbot.core.config.astrbot_config import AstrBotConfig
except ImportError:
    AstrBotConfig = dict  # type: ignore
from astrbot.core.platform.message_session import MessageSession
try:
    from astrbot.api.star import StarTools
except ImportError:
    StarTools = None
try:
    from .scheduler import SparkScheduler
except ImportError:  # pragma: no cover - direct execution
    from scheduler import SparkScheduler

@register("auto_spark", "AstrBot", "支持群聊和私聊多会话的自动续火", "1.1.0")
class AutoSparkPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        cfg = config or {}
        self.interval = max(10, int(cfg.get("interval_seconds", 3600)))
        self.message = str(cfg.get("message", "续火啦 🔥"))
        self.enabled = bool(cfg.get("enabled", True))
        self.admin_only = bool(cfg.get("admin_only", True))
        self.send_on_startup = bool(cfg.get("send_on_startup", False))
        self.send_times = self._parse_times(cfg.get("send_times", ""))
        if StarTools is not None:
            try:
                self._state_file = Path(StarTools.get_data_dir("astrbot_plugin_auto_spark")) / "targets.json"
            except Exception:
                self._state_file = Path("data/plugin_data/astrbot_plugin_auto_spark/targets.json")
        else:
            self._state_file = Path("data/plugin_data/astrbot_plugin_auto_spark/targets.json")
        configured = self._parse_targets(cfg.get("targets", ""))
        self.scheduler = SparkScheduler(self._send, self.interval, self.message, self.send_on_startup, self.send_times)
        self._configured_targets = configured

    @staticmethod
    def _parse_times(raw: Any) -> list[str]:
        values = raw if isinstance(raw, (list, tuple, set)) else str(raw or "").replace("，", "\n").replace(",", "\n").splitlines()
        result = []
        for value in values:
            try:
                hour, minute = map(int, str(value).strip().split(":", 1))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    result.append(f"{hour:02d}:{minute:02d}")
            except (TypeError, ValueError):
                continue
        return sorted(set(result))

    @staticmethod
    def _parse_targets(raw: Any) -> list[str]:
        vals = raw if isinstance(raw, (list, tuple, set)) else str(raw or "").replace("，", "\n").replace(",", "\n").splitlines()
        result = []
        for value in vals:
            umo = str(value).strip()
            if not umo:
                continue
            try:
                # Validate platform instance id, message type and session id.
                MessageSession.from_str(umo)
            except Exception:
                logger.warning("auto_spark: ignore invalid target UMO %r", umo)
                continue
            result.append(umo)
        return result

    async def initialize(self):
        if not self.enabled:
            return
        persisted = self._load_targets()
        for umo in dict.fromkeys(self._configured_targets + persisted):
            self.scheduler.start(umo)

    async def _send(self, umo: str, text: str) -> bool:
        return await self.context.send_message(umo, MessageChain([Plain(text)]))

    def _load_targets(self) -> list[str]:
        try:
            if self._state_file.exists():
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                return self._parse_targets(data.get("targets", []) if isinstance(data, dict) else data)
        except Exception as exc:
            logger.warning("auto_spark: load state failed: %s", exc)
        return []

    def _save_targets(self):
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(json.dumps({"targets": list(self.scheduler.targets)}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("auto_spark: save state failed: %s", exc)

    @filter.command("续火")
    async def manage(self, event: AstrMessageEvent):
        if self.admin_only and not event.is_admin():
            yield event.plain_result("仅管理员可以管理续火。")
            return
        parts = (event.get_message_str() or "").strip().split()
        action = parts[1].lower() if len(parts) > 1 else "状态"
        umo = event.unified_msg_origin
        if action in {"开启", "开", "on", "start"}:
            if len(parts) > 2:
                try:
                    self.interval = max(10, int(parts[2])); self.scheduler.interval = self.interval
                except ValueError:
                    pass
            created = self.scheduler.start(umo)
            self._save_targets()
            yield event.plain_result(f"续火已{'开启' if created else '在运行'}\n会话：{umo}\n" + (f"每天：{', '.join(self.send_times)}" if self.send_times else f"间隔：{self.interval} 秒"))
        elif action in {"关闭", "关", "off", "stop"}:
            stopped = await self.scheduler.stop(umo); self._save_targets()
            yield event.plain_result("续火已关闭" if stopped else "当前会话未开启续火")
        elif action in {"状态", "status", "list", "列表"}:
            state = "运行中" if umo in self.scheduler.targets else "未开启"
            yield event.plain_result(f"当前会话：{state}\n活动会话数：{len(self.scheduler.targets)}\n" + (f"每天：{', '.join(self.send_times)}" if self.send_times else f"间隔：{self.interval} 秒"))
        else:
            yield event.plain_result("用法：/续火 开启 [间隔秒]、/续火 关闭、/续火 状态；定时发送请在插件配置中填写 send_times")

    async def terminate(self):
        await self.scheduler.stop_all()
