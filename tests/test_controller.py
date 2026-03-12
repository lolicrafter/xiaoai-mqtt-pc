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
            topic="A001",
            aliases=["切到电视", "tv"],
            path=str(tmp_path / "demo.exe"),
        )
    )
    store.save(config)
    return AppController(store, LogService())


def test_match_action_by_alias(tmp_path):
    controller = build_controller(tmp_path)
    action = controller.match_action("A001", "切到电视")
    assert action is not None
    assert action.id == "open-tv"


def test_handle_unknown_message_creates_warning_log(tmp_path):
    controller = build_controller(tmp_path)
    controller.handle_message("A001", "unknown")
    entries = controller.log_service.entries()
    assert entries
    assert entries[0].level == "WARNING"
