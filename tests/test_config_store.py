import json

from xiaoai_desktop.config_store import ConfigStore
from xiaoai_desktop.models import ActionType, AppConfig, OpenAppAction, deserialize_config, serialize_config


def test_config_store_roundtrip(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig()
    config.curtain.on_action_id = "action-1"
    config.curtain.percent_actions["60"] = "action-1"
    config.actions.append(
        OpenAppAction(
            id="action-1",
            name="打开记事本",
            topic="A009",
            aliases=["open_notepad", "打开记事本"],
            path="C:/Windows/notepad.exe",
            args=[],
        )
    )
    store.save(config)

    loaded = store.load()
    assert loaded.actions[0].type == ActionType.OPEN_APP
    assert loaded.curtain.on_action_id == "action-1"
    assert loaded.curtain.percent_actions["60"] == "action-1"


def test_serialize_config_contains_action_type():
    config = AppConfig()
    config.actions.append(
        OpenAppAction(
            id="action-1",
            name="打开记事本",
            topic="A009",
            aliases=["open_notepad"],
            path="C:/Windows/notepad.exe",
        )
    )
    payload = serialize_config(config)
    assert payload["actions"][0]["type"] == "open_app"
    assert payload["curtain"]["topic"] == "A009"


def test_deserialize_config_converts_string_action_type():
    payload = {
        "mqtt": {},
        "app": {},
        "actions": [
            {
                "id": "action-1",
                "name": "打开记事本",
                "topic": "A001",
                "aliases": ["open_notepad"],
                "enabled": True,
                "type": "open_app",
                "path": "/tmp/demo",
                "args": [],
                "working_dir": "",
            }
        ],
    }
    config = deserialize_config(payload)
    assert config.actions[0].type == ActionType.OPEN_APP
