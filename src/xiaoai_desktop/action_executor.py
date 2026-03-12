from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable

from .log_service import LogService
from .models import (
    ActionModel,
    ActionType,
    CompositeAction,
    LogEntry,
    OpenAppAction,
    RunScriptAction,
    SwitchDisplayAction,
)


class ActionExecutor:
    def __init__(self, log_service: LogService) -> None:
        self.log_service = log_service

    def execute(self, action: ActionModel, actions_by_id: Dict[str, ActionModel], topic: str, payload: str) -> bool:
        try:
            if action.type == ActionType.OPEN_APP:
                self._execute_open_app(action)
            elif action.type == ActionType.RUN_SCRIPT:
                self._execute_script(action)
            elif action.type == ActionType.SWITCH_DISPLAY:
                self._execute_switch_display(action)
            elif action.type == ActionType.COMPOSITE:
                self._execute_composite(action, actions_by_id, topic, payload)
            else:
                raise ValueError(f"不支持的动作类型: {action.type}")
        except Exception as exc:  # noqa: BLE001
            self.log_service.add(
                LogEntry.create(
                    level="ERROR",
                    topic=topic,
                    payload=payload,
                    action_name=action.name,
                    success=False,
                    message=str(exc),
                )
            )
            return False

        self.log_service.add(
            LogEntry.create(
                level="INFO",
                topic=topic,
                payload=payload,
                action_name=action.name,
                success=True,
                message="执行成功",
            )
        )
        return True

    def _execute_open_app(self, action: OpenAppAction) -> None:
        command = [action.path, *action.args]
        self._spawn(command, action.working_dir or None)

    def _execute_script(self, action: RunScriptAction) -> None:
        script_path = Path(action.script_path)
        suffix = script_path.suffix.lower()
        if suffix == ".ps1":
            command = [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                *action.args,
            ]
        elif suffix in {".bat", ".cmd"}:
            command = ["cmd", "/c", str(script_path), *action.args]
        elif suffix == ".py":
            command = ["python", str(script_path), *action.args]
        else:
            command = [str(script_path), *action.args]
        self._spawn(command, action.working_dir or None)

    def _execute_switch_display(self, action: SwitchDisplayAction) -> None:
        command = [action.executable_path, action.profile_path, *action.args]
        self._spawn(command, None)

    def _execute_composite(
        self,
        action: CompositeAction,
        actions_by_id: Dict[str, ActionModel],
        topic: str,
        payload: str,
    ) -> None:
        for step in action.steps:
            child = actions_by_id.get(step.action_id)
            if child is None:
                raise ValueError(f"组合动作引用不存在的子动作: {step.action_id}")
            if child.id == action.id:
                raise ValueError("组合动作不能引用自身")
            if not self.execute(child, actions_by_id, topic, payload):
                raise RuntimeError(f"子动作执行失败: {child.name}")

    def _spawn(self, command: Iterable[str], working_dir: str | None) -> None:
        normalized = [part for part in command if part]
        if not normalized:
            raise ValueError("动作命令不能为空")
        executable = Path(normalized[0])
        if not executable.exists():
            raise FileNotFoundError(f"文件不存在: {executable}")
        cwd = working_dir or str(executable.parent)
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.Popen(
            normalized,
            cwd=cwd,
            shell=False,
            creationflags=creationflags,
        )
