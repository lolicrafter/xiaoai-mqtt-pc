from __future__ import annotations

from typing import Dict, List, Optional

from .action_executor import ActionExecutor
from .config_store import ConfigStore
from .log_service import LogService
from .models import ActionModel, AppConfig, LogEntry
from .mqtt_service import MqttService


class AppController:
    def __init__(self, store: ConfigStore, log_service: LogService) -> None:
        self.store = store
        self.log_service = log_service
        self.config = store.load()
        self.log_service.set_limit(self.config.app.log_limit)
        self.executor = ActionExecutor(log_service)
        self.mqtt_service = MqttService(self.config.mqtt, self.handle_message, self._log_status)

    def reload(self) -> None:
        self.config = self.store.load()
        self.log_service.set_limit(self.config.app.log_limit)

    def save(self) -> None:
        self.store.save(self.config)

    def start(self) -> None:
        if not self.config.mqtt.auto_connect:
            self._log_status("MQTT 自动连接已关闭")
            return
        topics = self.config.topics()
        if not topics:
            self._log_status("没有可订阅的主题")
            return
        self.mqtt_service.settings = self.config.mqtt
        self.mqtt_service.connect(topics)

    def stop(self) -> None:
        self.mqtt_service.disconnect()

    def actions(self) -> List[ActionModel]:
        return list(self.config.actions)

    def find_action(self, action_id: str) -> Optional[ActionModel]:
        for action in self.config.actions:
            if action.id == action_id:
                return action
        return None

    def actions_by_id(self) -> Dict[str, ActionModel]:
        return {action.id: action for action in self.config.actions}

    def handle_message(self, topic: str, payload: str) -> None:
        self.log_service.add(
            LogEntry.create(
                level="INFO",
                topic=topic,
                payload=payload,
                action_name="MQTT",
                success=True,
                message="收到 MQTT 消息",
            )
        )
        action = self.match_action(topic, payload)
        if action is None:
            self.log_service.add(
                LogEntry.create(
                    level="WARNING",
                    topic=topic,
                    payload=payload,
                    action_name="",
                    success=False,
                    message="未匹配到动作",
                )
            )
            return
        self.executor.execute(action, self.actions_by_id(), topic, payload)

    def match_action(self, topic: str, payload: str) -> Optional[ActionModel]:
        if topic != self.config.curtain.topic:
            return None
        action_id = self.resolve_curtain_action_id(payload)
        if not action_id:
            return None
        action = self.find_action(action_id)
        if action is None or not action.enabled:
            return None
        return action

    def resolve_curtain_action_id(self, payload: str) -> str:
        normalized = payload.strip().lower()
        if normalized == "on":
            return self.config.curtain.on_action_id
        if normalized == "off":
            return self.config.curtain.off_action_id
        if normalized.startswith("on#"):
            percent = normalized[3:]
            return self.config.curtain.percent_actions.get(percent, "")
        return ""

    def trigger_curtain_message(self, payload: str) -> None:
        self.handle_message(self.config.curtain.topic, payload)

    def _log_status(self, message: str) -> None:
        self.log_service.add(
            LogEntry.create(
                level="INFO",
                topic="",
                payload="",
                action_name="系统",
                success=True,
                message=message,
            )
        )
