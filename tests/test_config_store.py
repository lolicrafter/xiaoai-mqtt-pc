import json

from xiaoai_desktop.config_store import ConfigStore
from xiaoai_desktop.models import ActionType, AppConfig, OpenAppAction, serialize_config


def test_config_store_roundtrip(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig()
    config.actions.append(
        OpenAppAction(
            id="action-1",
            name="打开记事本",
            topic="A001",
            aliases=["open_notepad", "打开记事本"],
            path="C:/Windows/notepad.exe",
            args=[],
        )
    )
    store.save(config)

    loaded = store.load()
    assert loaded.actions[0].type == ActionType.OPEN_APP
    assert loaded.actions[0].aliases == ["open_notepad", "打开记事本"]


def test_serialize_config_contains_action_type():
    config = AppConfig()
    config.actions.append(
        OpenAppAction(
            id="action-1",
            name="打开记事本",
            topic="A001",
            aliases=["open_notepad"],
            path="C:/Windows/notepad.exe",
        )
    )
    payload = serialize_config(config)
    assert payload["actions"][0]["type"] == "open_app"
