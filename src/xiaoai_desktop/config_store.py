from __future__ import annotations

import json
from pathlib import Path

from .models import AppConfig, default_config_path, deserialize_config, serialize_config


class ConfigStore:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or default_config_path()

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            config = AppConfig()
            self.save(config)
            return config
        with self.config_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return deserialize_config(payload)

    def save(self, config: AppConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(serialize_config(config), file, indent=2, ensure_ascii=False)
