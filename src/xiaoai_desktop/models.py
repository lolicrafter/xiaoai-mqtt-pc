from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class ActionType(str, Enum):
    OPEN_APP = "open_app"
    RUN_SCRIPT = "run_script"
    SWITCH_DISPLAY = "switch_display"
    COMPOSITE = "composite"


@dataclass
class MqttSettings:
    host: str = "bemfa.com"
    port: int = 9501
    client_id: str = ""
    username: str = "userName"
    password: str = "passwd"
    auto_connect: bool = True


@dataclass
class BaseAction:
    id: str
    name: str
    topic: str
    aliases: List[str] = field(default_factory=list)
    enabled: bool = True
    type: ActionType = ActionType.OPEN_APP

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["type"] = self.type.value
        return payload


@dataclass
class OpenAppAction(BaseAction):
    path: str = ""
    args: List[str] = field(default_factory=list)
    working_dir: str = ""
    type: ActionType = ActionType.OPEN_APP


@dataclass
class RunScriptAction(BaseAction):
    script_path: str = ""
    args: List[str] = field(default_factory=list)
    working_dir: str = ""
    type: ActionType = ActionType.RUN_SCRIPT


@dataclass
class SwitchDisplayAction(BaseAction):
    executable_path: str = ""
    profile_path: str = ""
    args: List[str] = field(default_factory=list)
    type: ActionType = ActionType.SWITCH_DISPLAY


@dataclass
class CompositeStep:
    action_id: str


@dataclass
class CompositeAction(BaseAction):
    steps: List[CompositeStep] = field(default_factory=list)
    type: ActionType = ActionType.COMPOSITE

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["steps"] = [asdict(step) for step in self.steps]
        return payload


ActionModel = Union[OpenAppAction, RunScriptAction, SwitchDisplayAction, CompositeAction]


@dataclass
class LogEntry:
    timestamp: str
    level: str
    topic: str
    payload: str
    action_name: str
    success: bool
    message: str

    @classmethod
    def create(
        cls,
        *,
        level: str,
        topic: str,
        payload: str,
        action_name: str,
        success: bool,
        message: str,
    ) -> "LogEntry":
        return cls(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level=level,
            topic=topic,
            payload=payload,
            action_name=action_name,
            success=success,
            message=message,
        )


@dataclass
class AppSettings:
    start_minimized: bool = True
    enable_autostart: bool = False
    log_limit: int = 200


@dataclass
class AppConfig:
    mqtt: MqttSettings = field(default_factory=MqttSettings)
    app: AppSettings = field(default_factory=AppSettings)
    actions: List[ActionModel] = field(default_factory=list)

    def topics(self) -> List[str]:
        return sorted({action.topic for action in self.actions if action.enabled and action.topic})


ACTION_TYPE_MAP = {
    ActionType.OPEN_APP.value: OpenAppAction,
    ActionType.RUN_SCRIPT.value: RunScriptAction,
    ActionType.SWITCH_DISPLAY.value: SwitchDisplayAction,
    ActionType.COMPOSITE.value: CompositeAction,
}


def default_config_path() -> Path:
    base_dir = Path.home() / "AppData" / "Roaming" / "XiaoAiDesktop" if _is_windows() else Path.home() / ".xiaoai-desktop"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "config.json"


def create_action(action_type: ActionType, *, name: str = "", topic: str = "", aliases: Optional[List[str]] = None) -> ActionModel:
    action_id = uuid4().hex
    aliases = aliases or []
    if action_type == ActionType.OPEN_APP:
        return OpenAppAction(id=action_id, name=name or "新建打开软件动作", topic=topic, aliases=aliases)
    if action_type == ActionType.RUN_SCRIPT:
        return RunScriptAction(id=action_id, name=name or "新建脚本动作", topic=topic, aliases=aliases)
    if action_type == ActionType.SWITCH_DISPLAY:
        return SwitchDisplayAction(id=action_id, name=name or "新建显示器切换动作", topic=topic, aliases=aliases)
    return CompositeAction(id=action_id, name=name or "新建组合动作", topic=topic, aliases=aliases)


def action_from_dict(raw: Dict[str, Any]) -> ActionModel:
    action_type = raw.get("type", ActionType.OPEN_APP.value)
    model_cls = ACTION_TYPE_MAP[action_type]
    if model_cls is CompositeAction:
        steps = [CompositeStep(**step) for step in raw.get("steps", [])]
        payload = {**raw, "steps": steps}
    else:
        payload = raw
    return model_cls(**payload)


def serialize_config(config: AppConfig) -> Dict[str, Any]:
    return {
        "mqtt": asdict(config.mqtt),
        "app": asdict(config.app),
        "actions": [action.to_dict() for action in config.actions],
    }


def deserialize_config(payload: Dict[str, Any]) -> AppConfig:
    mqtt = MqttSettings(**payload.get("mqtt", {}))
    app = AppSettings(**payload.get("app", {}))
    actions = [action_from_dict(raw) for raw in payload.get("actions", [])]
    return AppConfig(mqtt=mqtt, app=app, actions=actions)


def _is_windows() -> bool:
    return sys.platform == "win32"
