from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QStyle,
    QTableWidgetSelectionRange,
    QVBoxLayout,
    QWidget,
)

from .autostart import disable_autostart, enable_autostart, is_autostart_enabled
from .controller import AppController
from .models import (
    ActionType,
    CompositeAction,
    CompositeStep,
    LogEntry,
    OpenAppAction,
    RunScriptAction,
    SwitchDisplayAction,
    create_action,
)


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self.current_action_id: str | None = None
        self._is_quitting = False
        self.setWindowTitle("小爱桌面控制中心")
        self.resize(980, 720)
        self.controller.log_service.subscribe(self.append_log)
        self._build_ui()
        self._create_tray()
        self.refresh_curtain_mapping()
        self.refresh_actions()
        self.refresh_mqtt_fields()
        self.refresh_logs()

    def _set_wide_controls(self, *widgets: QWidget) -> None:
        for widget in widgets:
            widget.setMinimumWidth(320)

    def _load_app_icon(self) -> QIcon:
        icon_candidates = [
            self._resource_root() / "裁剪的圆形图片.png",
            self._resource_root() / "favicon.ico",
        ]
        for icon_path in icon_candidates:
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    return icon
        return self.style().standardIcon(QStyle.SP_ComputerIcon)

    def _resource_root(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return Path(__file__).resolve().parents[2]

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._build_curtain_tab(), "窗帘映射")
        tabs.addTab(self._build_actions_tab(), "动作库")
        tabs.addTab(self._build_mqtt_tab(), "MQTT")
        tabs.addTab(self._build_system_tab(), "系统")
        tabs.addTab(self._build_logs_tab(), "日志")
        self.setCentralWidget(tabs)

    def _build_curtain_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        info = QLabel("固定监听巴法云窗帘设备 A009。请把“开 / 关 / 打开到某百分比”分别绑定到一个已有动作。")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.curtain_topic_label = QLabel("A009")
        self.on_action_combo = QComboBox()
        self.off_action_combo = QComboBox()
        self._set_wide_controls(self.on_action_combo, self.off_action_combo)
        form.addRow("设备 ID", self.curtain_topic_label)
        form.addRow("开（on）", self.on_action_combo)
        form.addRow("关（off）", self.off_action_combo)
        layout.addLayout(form)

        percent_box = QGroupBox("打开幅度映射")
        percent_layout = QVBoxLayout(percent_box)
        add_row = QHBoxLayout()
        self.percent_spin = QSpinBox()
        self.percent_spin.setRange(0, 100)
        self.percent_action_combo = QComboBox()
        self._set_wide_controls(self.percent_action_combo)
        add_percent_button = QPushButton("添加/更新")
        add_percent_button.clicked.connect(self._save_percent_mapping)
        add_row.addWidget(QLabel("百分比"))
        add_row.addWidget(self.percent_spin)
        add_row.addWidget(self.percent_action_combo)
        add_row.addWidget(add_percent_button)
        percent_layout.addLayout(add_row)

        self.percent_table = QTableWidget(0, 2)
        self.percent_table.setHorizontalHeaderLabels(["百分比", "绑定动作"])
        self.percent_table.horizontalHeader().setStretchLastSection(True)
        self.percent_table.itemSelectionChanged.connect(self._on_percent_row_selected)
        percent_layout.addWidget(self.percent_table)

        percent_button_row = QHBoxLayout()
        remove_percent_button = QPushButton("删除选中映射")
        remove_percent_button.clicked.connect(self._remove_percent_mapping)
        percent_button_row.addWidget(remove_percent_button)
        percent_layout.addLayout(percent_button_row)
        layout.addWidget(percent_box)

        test_box = QGroupBox("测试触发")
        test_layout = QHBoxLayout(test_box)
        test_on_button = QPushButton("测试 on")
        test_on_button.clicked.connect(lambda: self._test_curtain_payload("on"))
        test_off_button = QPushButton("测试 off")
        test_off_button.clicked.connect(lambda: self._test_curtain_payload("off"))
        self.test_percent_spin = QSpinBox()
        self.test_percent_spin.setRange(0, 100)
        test_percent_button = QPushButton("测试 on#百分比")
        test_percent_button.clicked.connect(self._test_percent_payload)
        test_layout.addWidget(test_on_button)
        test_layout.addWidget(test_off_button)
        test_layout.addWidget(self.test_percent_spin)
        test_layout.addWidget(test_percent_button)
        layout.addWidget(test_box)

        save_button = QPushButton("保存窗帘映射")
        save_button.clicked.connect(self._save_curtain_mapping)
        layout.addWidget(save_button)
        layout.addStretch(1)
        return page

    def _build_actions_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)

        left_layout = QVBoxLayout()
        self.action_list = QListWidget()
        self.action_list.currentItemChanged.connect(self._on_action_selected)
        left_layout.addWidget(self.action_list)

        button_row = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItem("打开软件", ActionType.OPEN_APP)
        self.type_combo.addItem("运行脚本", ActionType.RUN_SCRIPT)
        self.type_combo.addItem("切换显示器", ActionType.SWITCH_DISPLAY)
        self.type_combo.addItem("组合动作", ActionType.COMPOSITE)
        button_row.addWidget(self.type_combo)

        add_button = QPushButton("新增动作")
        add_button.clicked.connect(self._add_action)
        button_row.addWidget(add_button)

        delete_button = QPushButton("删除动作")
        delete_button.clicked.connect(self._delete_action)
        button_row.addWidget(delete_button)
        left_layout.addLayout(button_row)

        layout.addLayout(left_layout, 1)

        right_panel = QWidget()
        form = QFormLayout(right_panel)
        self.name_edit = QLineEdit()
        self.enabled_checkbox = QCheckBox("启用此动作")
        self.enabled_checkbox.setChecked(True)
        self.primary_path_edit = QLineEdit()
        self.args_edit = QLineEdit()
        self.working_dir_edit = QLineEdit()
        self.profile_path_edit = QLineEdit()
        self.step_action_combo = QComboBox()
        self.steps_list = QListWidget()
        steps_box = self._build_steps_box()
        self._set_wide_controls(
            self.name_edit,
            self.primary_path_edit,
            self.args_edit,
            self.working_dir_edit,
            self.profile_path_edit,
            self.step_action_combo,
        )

        form.addRow("动作名称", self.name_edit)
        form.addRow("", self.enabled_checkbox)
        form.addRow("主路径", self.primary_path_edit)
        form.addRow("参数（空格分隔）", self.args_edit)
        form.addRow("工作目录", self.working_dir_edit)
        form.addRow("配置文件路径", self.profile_path_edit)
        form.addRow("组合动作步骤", steps_box)

        save_button = QPushButton("保存当前动作")
        save_button.clicked.connect(self._save_current_action)
        form.addRow("", save_button)

        tip = QLabel("切换显示器类型：主路径填 MonitorSwitcher 可执行文件，配置文件路径填 profile。")
        tip.setWordWrap(True)
        form.addRow("", tip)

        layout.addWidget(right_panel, 2)
        return page

    def _build_steps_box(self) -> QWidget:
        box = QGroupBox("可视化步骤编排")
        box_layout = QVBoxLayout(box)
        selector_row = QHBoxLayout()
        selector_row.addWidget(self.step_action_combo)
        add_step_button = QPushButton("加入步骤")
        add_step_button.clicked.connect(self._add_composite_step)
        selector_row.addWidget(add_step_button)
        box_layout.addLayout(selector_row)
        box_layout.addWidget(self.steps_list)

        move_row = QHBoxLayout()
        up_button = QPushButton("上移")
        up_button.clicked.connect(lambda: self._move_composite_step(-1))
        down_button = QPushButton("下移")
        down_button.clicked.connect(lambda: self._move_composite_step(1))
        remove_button = QPushButton("移除步骤")
        remove_button.clicked.connect(self._remove_composite_step)
        move_row.addWidget(up_button)
        move_row.addWidget(down_button)
        move_row.addWidget(remove_button)
        box_layout.addLayout(move_row)
        return box

    def _build_mqtt_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.host_edit = QLineEdit()
        self.port_edit = QSpinBox()
        self.port_edit.setMaximum(65535)
        self.client_id_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.auto_connect_checkbox = QCheckBox("启动后自动连接")
        self._set_wide_controls(
            self.host_edit,
            self.client_id_edit,
            self.username_edit,
            self.password_edit,
        )
        connect_button = QPushButton("保存并重连")
        connect_button.clicked.connect(self._save_mqtt)

        form.addRow("主机", self.host_edit)
        form.addRow("端口", self.port_edit)
        form.addRow("巴法云私钥", self.client_id_edit)
        form.addRow("用户名", self.username_edit)
        form.addRow("密码", self.password_edit)
        form.addRow("", self.auto_connect_checkbox)
        form.addRow("", connect_button)
        return page

    def _build_system_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.start_minimized_checkbox = QCheckBox("启动时最小化到托盘")
        self.autostart_checkbox = QCheckBox("开机自启动")
        self.log_limit_spin = QSpinBox()
        self.log_limit_spin.setRange(50, 1000)
        save_button = QPushButton("保存系统设置")
        save_button.clicked.connect(self._save_system_settings)
        status_label = QLabel("建议在动作与 MQTT 配置完成后再启用开机自启。")
        status_label.setWordWrap(True)
        layout.addWidget(self.start_minimized_checkbox)
        layout.addWidget(self.autostart_checkbox)
        layout.addWidget(QLabel("日志保留条数"))
        layout.addWidget(self.log_limit_spin)
        layout.addWidget(save_button)
        layout.addWidget(status_label)
        layout.addStretch(1)
        return page

    def _build_logs_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.log_table = QTableWidget(0, 6)
        self.log_table.setHorizontalHeaderLabels(["时间", "级别", "主题", "载荷", "动作", "结果"])
        self.log_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.log_table)
        return page

    def _create_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        tray_icon = self._load_app_icon()
        self.setWindowIcon(tray_icon)
        self.tray_icon.setIcon(tray_icon)
        self.tray_icon.setToolTip("小爱桌面控制中心")
        menu = self.tray_icon.contextMenu() or None
        if menu is None:
            from PySide6.QtWidgets import QMenu

            menu = QMenu(self)
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh_system_settings()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._is_quitting:
            event.accept()
            return
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("小爱桌面控制中心", "程序已最小化到托盘", QSystemTrayIcon.Information, 2000)

    def append_log(self, entry: LogEntry) -> None:
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        values = [
            entry.timestamp,
            entry.level,
            entry.topic,
            entry.payload,
            entry.action_name,
            entry.message if entry.success else f"失败: {entry.message}",
        ]
        for column, value in enumerate(values):
            self.log_table.setItem(row, column, QTableWidgetItem(value))
        self.log_table.scrollToTop()

    def refresh_logs(self) -> None:
        self.log_table.setRowCount(0)
        for entry in self.controller.log_service.entries():
            self.append_log(entry)

    def refresh_mqtt_fields(self) -> None:
        mqtt = self.controller.config.mqtt
        self.host_edit.setText(mqtt.host)
        self.port_edit.setValue(mqtt.port)
        self.client_id_edit.setText(mqtt.client_id)
        self.username_edit.setText(mqtt.username)
        self.password_edit.setText(mqtt.password)
        self.auto_connect_checkbox.setChecked(mqtt.auto_connect)

    def refresh_system_settings(self) -> None:
        app = self.controller.config.app
        self.start_minimized_checkbox.setChecked(app.start_minimized)
        self.autostart_checkbox.setChecked(is_autostart_enabled())
        self.log_limit_spin.setValue(app.log_limit)

    def refresh_actions(self) -> None:
        previous_id = self.current_action_id
        self.action_list.clear()
        for action in self.controller.actions():
            item = QListWidgetItem(f"{action.name} [{action.type.value}]")
            item.setData(Qt.UserRole, action.id)
            self.action_list.addItem(item)
        if previous_id:
            for index in range(self.action_list.count()):
                item = self.action_list.item(index)
                if item.data(Qt.UserRole) == previous_id:
                    self.action_list.setCurrentItem(item)
                    break

    def _on_action_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        del previous
        if current is None:
            self.current_action_id = None
            return
        self.current_action_id = current.data(Qt.UserRole)
        action = self.controller.find_action(self.current_action_id)
        if action is None:
            return
        self._refresh_step_action_combo()
        self.name_edit.setText(action.name)
        self.enabled_checkbox.setChecked(action.enabled)
        self.primary_path_edit.clear()
        self.args_edit.clear()
        self.working_dir_edit.clear()
        self.profile_path_edit.clear()
        self.steps_list.clear()
        if isinstance(action, OpenAppAction):
            self.primary_path_edit.setText(action.path)
            self.args_edit.setText(" ".join(action.args))
            self.working_dir_edit.setText(action.working_dir)
        elif isinstance(action, RunScriptAction):
            self.primary_path_edit.setText(action.script_path)
            self.args_edit.setText(" ".join(action.args))
            self.working_dir_edit.setText(action.working_dir)
        elif isinstance(action, SwitchDisplayAction):
            self.primary_path_edit.setText(action.executable_path)
            self.profile_path_edit.setText(action.profile_path)
            self.args_edit.setText(" ".join(action.args))
        elif isinstance(action, CompositeAction):
            self._populate_steps(action.steps)
        self._toggle_composite_fields(isinstance(action, CompositeAction))

    def _add_action(self) -> None:
        action_type = self.type_combo.currentData()
        action = create_action(action_type)
        self.controller.config.actions.append(action)
        self.controller.save()
        self.refresh_actions()
        self._refresh_step_action_combo()

    def _delete_action(self) -> None:
        if self.current_action_id is None:
            return
        if self._is_action_referenced(self.current_action_id):
            QMessageBox.warning(self, "无法删除", "该动作已被组合动作引用，请先移除组合动作中的引用。")
            return
        self.controller.config.actions = [item for item in self.controller.config.actions if item.id != self.current_action_id]
        self.controller.save()
        self.current_action_id = None
        self.refresh_actions()
        self._refresh_step_action_combo()

    def _save_current_action(self) -> None:
        if self.current_action_id is None:
            QMessageBox.warning(self, "未选择动作", "请先在左侧选择一个动作。")
            return
        action = self.controller.find_action(self.current_action_id)
        if action is None:
            return
        action.name = self.name_edit.text().strip()
        action.enabled = self.enabled_checkbox.isChecked()
        args = [item for item in self.args_edit.text().split(" ") if item]
        if isinstance(action, OpenAppAction):
            action.path = self.primary_path_edit.text().strip()
            action.args = args
            action.working_dir = self.working_dir_edit.text().strip()
        elif isinstance(action, RunScriptAction):
            action.script_path = self.primary_path_edit.text().strip()
            action.args = args
            action.working_dir = self.working_dir_edit.text().strip()
        elif isinstance(action, SwitchDisplayAction):
            action.executable_path = self.primary_path_edit.text().strip()
            action.profile_path = self.profile_path_edit.text().strip()
            action.args = args
        elif isinstance(action, CompositeAction):
            action.steps = self._read_steps_from_list()
        self.controller.save()
        self.controller.stop()
        self.controller.start()
        self.refresh_actions()
        self.refresh_curtain_mapping()

    def _save_mqtt(self) -> None:
        mqtt = self.controller.config.mqtt
        mqtt.host = self.host_edit.text().strip()
        mqtt.port = self.port_edit.value()
        mqtt.client_id = self.client_id_edit.text().strip()
        mqtt.username = self.username_edit.text().strip()
        mqtt.password = self.password_edit.text().strip()
        mqtt.auto_connect = self.auto_connect_checkbox.isChecked()
        self.controller.save()
        self.controller.stop()
        self.controller.start()

    def _save_system_settings(self) -> None:
        app = self.controller.config.app
        app.start_minimized = self.start_minimized_checkbox.isChecked()
        app.enable_autostart = self.autostart_checkbox.isChecked()
        app.log_limit = self.log_limit_spin.value()
        self.controller.log_service.set_limit(app.log_limit)
        self.controller.save()
        if app.enable_autostart:
            enable_autostart()
        else:
            disable_autostart()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.showNormal()
            self.activateWindow()

    def _quit_app(self) -> None:
        self.controller.stop()
        self.tray_icon.hide()
        self._is_quitting = True
        QApplication.instance().quit()

    def _refresh_step_action_combo(self) -> None:
        self.step_action_combo.clear()
        for action in self.controller.actions():
            if action.id == self.current_action_id:
                continue
            self.step_action_combo.addItem(f"{action.name} [{action.type.value}] ({action.id})", action.id)

    def refresh_curtain_mapping(self) -> None:
        curtain = self.controller.config.curtain
        self.curtain_topic_label.setText(curtain.topic)
        self._refresh_action_selector(self.on_action_combo, curtain.on_action_id)
        self._refresh_action_selector(self.off_action_combo, curtain.off_action_id)
        self._refresh_action_selector(self.percent_action_combo, "")
        self._refresh_percent_table()

    def _refresh_action_selector(self, combo: QComboBox, selected_action_id: str) -> None:
        combo.clear()
        combo.addItem("未绑定", "")
        for action in self.controller.actions():
            combo.addItem(f"{action.name} [{action.type.value}]", action.id)
        index = combo.findData(selected_action_id)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _refresh_percent_table(self) -> None:
        percent_actions = self.controller.config.curtain.percent_actions
        self.percent_table.setRowCount(0)
        for percent in sorted(percent_actions.keys(), key=lambda value: int(value)):
            action_id = percent_actions[percent]
            action = self.controller.find_action(action_id)
            action_name = f"{action.name} [{action.type.value}]" if action else f"缺失动作 ({action_id})"
            row = self.percent_table.rowCount()
            self.percent_table.insertRow(row)
            percent_item = QTableWidgetItem(percent)
            percent_item.setData(Qt.UserRole, percent)
            self.percent_table.setItem(row, 0, percent_item)
            self.percent_table.setItem(row, 1, QTableWidgetItem(action_name))

    def _save_curtain_mapping(self) -> None:
        curtain = self.controller.config.curtain
        curtain.on_action_id = self.on_action_combo.currentData()
        curtain.off_action_id = self.off_action_combo.currentData()
        self.controller.save()
        self.controller.stop()
        self.controller.start()
        QMessageBox.information(self, "保存成功", "窗帘映射已保存。")

    def _save_percent_mapping(self) -> None:
        action_id = self.percent_action_combo.currentData()
        if not action_id:
            QMessageBox.warning(self, "未选择动作", "请先为该百分比选择一个动作。")
            return
        percent = str(self.percent_spin.value())
        self.controller.config.curtain.percent_actions[percent] = action_id
        self.controller.save()
        self._refresh_percent_table()

    def _remove_percent_mapping(self) -> None:
        current_row = self.percent_table.currentRow()
        if current_row < 0:
            return
        percent_item = self.percent_table.item(current_row, 0)
        if percent_item is None:
            return
        percent = percent_item.data(Qt.UserRole)
        self.controller.config.curtain.percent_actions.pop(str(percent), None)
        self.controller.save()
        self._refresh_percent_table()

    def _on_percent_row_selected(self) -> None:
        current_row = self.percent_table.currentRow()
        if current_row < 0:
            return
        percent_item = self.percent_table.item(current_row, 0)
        if percent_item is None:
            return
        percent = int(percent_item.text())
        self.percent_spin.setValue(percent)
        action_id = self.controller.config.curtain.percent_actions.get(str(percent), "")
        index = self.percent_action_combo.findData(action_id)
        self.percent_action_combo.setCurrentIndex(index if index >= 0 else 0)

    def _test_curtain_payload(self, payload: str) -> None:
        self.controller.trigger_curtain_message(payload)

    def _test_percent_payload(self) -> None:
        self._test_curtain_payload(f"on#{self.test_percent_spin.value()}")

    def _populate_steps(self, steps: List[CompositeStep]) -> None:
        self.steps_list.clear()
        for step in steps:
            action = self.controller.find_action(step.action_id)
            if action is None:
                label = f"缺失动作 ({step.action_id})"
            else:
                label = f"{action.name} [{action.type.value}] ({action.id})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, step.action_id)
            self.steps_list.addItem(item)

    def _read_steps_from_list(self) -> List[CompositeStep]:
        steps: List[CompositeStep] = []
        for index in range(self.steps_list.count()):
            action_id = self.steps_list.item(index).data(Qt.UserRole)
            if action_id:
                steps.append(CompositeStep(action_id=action_id))
        return steps

    def _add_composite_step(self) -> None:
        action_id = self.step_action_combo.currentData()
        if not action_id:
            return
        action = self.controller.find_action(action_id)
        if action is None:
            return
        item = QListWidgetItem(f"{action.name} [{action.type.value}] ({action.id})")
        item.setData(Qt.UserRole, action.id)
        self.steps_list.addItem(item)

    def _remove_composite_step(self) -> None:
        row = self.steps_list.currentRow()
        if row >= 0:
            self.steps_list.takeItem(row)

    def _move_composite_step(self, offset: int) -> None:
        current_row = self.steps_list.currentRow()
        target_row = current_row + offset
        if current_row < 0 or target_row < 0 or target_row >= self.steps_list.count():
            return
        item = self.steps_list.takeItem(current_row)
        self.steps_list.insertItem(target_row, item)
        self.steps_list.setCurrentRow(target_row)

    def _toggle_composite_fields(self, is_composite: bool) -> None:
        self.step_action_combo.setEnabled(is_composite)
        self.steps_list.setEnabled(is_composite)

    def _is_action_referenced(self, action_id: str) -> bool:
        for action in self.controller.actions():
            if not isinstance(action, CompositeAction):
                continue
            if any(step.action_id == action_id for step in action.steps):
                return True
        return False
