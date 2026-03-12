from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from .config_store import ConfigStore
from .controller import AppController
from .log_service import LogService
from .main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="小爱桌面控制中心")
    parser.add_argument("--minimized", action="store_true", help="启动后最小化到托盘")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    app = QApplication(sys.argv)
    store = ConfigStore()
    initial_config = store.load()
    log_service = LogService(limit=initial_config.app.log_limit)
    controller = AppController(store, log_service)
    window = MainWindow(controller)
    controller.start()
    if not (args.minimized or controller.config.app.start_minimized):
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
