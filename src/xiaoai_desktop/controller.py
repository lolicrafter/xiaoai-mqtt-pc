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
        normalized = payload.strip().lower()
        for action in self.config.actions:
            if not action.enabled or action.topic != topic:
                continue
            aliases = {alias.strip().lower() for alias in action.aliases if alias.strip()}
            if normalized in aliases:
                return action
        return None

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
