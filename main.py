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
from astrbot.core.platform.message_type import MessageType
try:
    from astrbot.api.star import StarTools
except ImportError:
    StarTools = None
try:
    from .scheduler import SparkScheduler
except ImportError:
    from scheduler import SparkScheduler

@register("auto_spark", "AstrBot", "每天向多个群聊和私聊发送一次续火消息", "2.0.0")
class AutoSparkPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        cfg = config or {}
        self.message = str(cfg.get("message", "续火啦 🔥"))
        self.enabled = bool(cfg.get("enabled", True))
        self.admin_only = bool(cfg.get("admin_only", True))
        self.send_time = self._parse_time(cfg.get("send_time", "09:00")) or "09:00"
        if StarTools is not None:
            try: self._state_file = Path(StarTools.get_data_dir("astrbot_plugin_auto_spark")) / "targets.json"
            except Exception: self._state_file = Path("data/plugin_data/astrbot_plugin_auto_spark/targets.json")
        else: self._state_file = Path("data/plugin_data/astrbot_plugin_auto_spark/targets.json")
        self.platform_id = str(cfg.get("platform_id", "")).strip()
        self.group_targets = self._parse_targets(cfg.get("group_targets", []), "GroupMessage", self.platform_id)
        self.private_targets = self._parse_targets(cfg.get("private_targets", []), "FriendMessage", self.platform_id)
        self._load_targets()
        self.scheduler = SparkScheduler(self._send_group, self._send_private, self.message, self.send_time, target_provider=lambda: (self.group_targets, self.private_targets))

    @staticmethod
    def _parse_time(raw: Any) -> str | None:
        try:
            hour, minute = map(int, str(raw).strip().split(":", 1))
            return f"{hour:02d}:{minute:02d}" if 0 <= hour <= 23 and 0 <= minute <= 59 else None
        except (TypeError, ValueError): return None

    @staticmethod
    def _parse_targets(raw: Any, expected_type: str, platform_id: str = "") -> list[str]:
        vals = raw if isinstance(raw, (list, tuple, set)) else str(raw or "").replace("，", "\n").replace(",", "\n").splitlines()
        result = []
        for value in vals:
            value = str(value).strip()
            if not value: continue
            umo = value
            if ":" not in value and platform_id:
                message_type = MessageType.GROUP_MESSAGE if expected_type == "GroupMessage" else MessageType.FRIEND_MESSAGE
                umo = str(MessageSession(platform_id, message_type, value))
            try:
                session = MessageSession.from_str(umo)
                if session.message_type.value != expected_type: raise ValueError("wrong message type")
            except Exception:
                logger.warning("auto_spark: ignore invalid %s target %r", expected_type, umo); continue
            if umo not in result: result.append(umo)
        return result

    async def initialize(self):
        if self.enabled: self.scheduler.start()

    async def _send_group(self, umo: str, text: str) -> bool:
        return bool(await self.context.send_message(umo, MessageChain([Plain(text)])))

    async def _send_private(self, umo: str, text: str) -> bool:
        return bool(await self.context.send_message(umo, MessageChain([Plain(text)])))

    def _load_targets(self):
        try:
            if self._state_file.exists():
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.group_targets = list(dict.fromkeys(self.group_targets + self._parse_targets(data.get("group_targets", []), "GroupMessage", self.platform_id)))
                    self.private_targets = list(dict.fromkeys(self.private_targets + self._parse_targets(data.get("private_targets", []), "FriendMessage", self.platform_id)))
        except Exception as exc: logger.warning("auto_spark: load state failed: %s", exc)

    def _event_umo(self, event: AstrMessageEvent) -> str:
        platform = str(event.get_platform_id())
        if event.get_group_id():
            return str(MessageSession(platform, MessageType.GROUP_MESSAGE, str(event.get_group_id())))
        return str(MessageSession(platform, MessageType.FRIEND_MESSAGE, str(event.get_sender_id())))

    def _save_targets(self):
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(json.dumps({"group_targets": self.group_targets, "private_targets": self.private_targets}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc: logger.warning("auto_spark: save state failed: %s", exc)

    async def _send_all_now(self):
        return await self.scheduler.send_once(self.group_targets, self.private_targets)

    @filter.command("续火")
    async def manage(self, event: AstrMessageEvent):
        if self.admin_only and not event.is_admin():
            yield event.plain_result("仅管理员可以管理续火。"); return
        parts = (event.get_message_str() or "").strip().split()
        action = parts[1].lower() if len(parts) > 1 else "状态"
        umo = self._event_umo(event)
        if action in {"开启", "开", "on", "start"}:
            target_type = "GroupMessage" if ":GroupMessage:" in umo else "FriendMessage"
            target_list = self.group_targets if target_type == "GroupMessage" else self.private_targets
            if umo not in target_list: target_list.append(umo)
            self._save_targets(); self.scheduler.start()
            yield event.plain_result(f"续火已开启。\n会话：{umo}\n每天发送：{self.send_time}")
        elif action in {"关闭", "关", "off", "stop"}:
            target_list = self.group_targets if ":GroupMessage:" in umo else self.private_targets
            if umo in target_list: target_list.remove(umo); self._save_targets(); reply = "当前会话已关闭续火。"
            else: reply = "当前会话未开启续火。"
            yield event.plain_result(reply)
        elif action in {"状态", "status", "list", "列表"}:
            yield event.plain_result(f"群聊目标：{len(self.group_targets)} 个\n私聊目标：{len(self.private_targets)} 个\n每天发送：{self.send_time}")
        else: yield event.plain_result("用法：/续火 开启、/续火 关闭、/续火 状态")

    async def terminate(self): await self.scheduler.stop()
