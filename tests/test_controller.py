from xiaoai_desktop.config_store import ConfigStore
from xiaoai_desktop.controller import AppController
from xiaoai_desktop.log_service import LogService
from xiaoai_desktop.models import AppConfig, OpenAppAction


def build_controller(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig()
    config.actions.append(
        OpenAppAction(
            id="open-tv",
            name="切到电视",
            topic="A009",
            aliases=["切到电视", "tv"],
            path=str(tmp_path / "demo.exe"),
        )
    )
    config.curtain.on_action_id = "open-tv"
    config.curtain.percent_actions["60"] = "open-tv"
    store.save(config)
    return AppController(store, LogService())


def test_match_action_by_on_mapping(tmp_path):
    controller = build_controller(tmp_path)
    action = controller.match_action("A009", "on")
    assert action is not None
    assert action.id == "open-tv"


def test_handle_unknown_message_creates_warning_log(tmp_path):
    controller = build_controller(tmp_path)
    controller.handle_message("A009", "unknown")
    entries = controller.log_service.entries()
    assert entries
    assert entries[0].level == "WARNING"


def test_match_action_by_percent_mapping(tmp_path):
    controller = build_controller(tmp_path)
    action = controller.match_action("A009", "on#60")
    assert action is not None
    assert action.id == "open-tv"
