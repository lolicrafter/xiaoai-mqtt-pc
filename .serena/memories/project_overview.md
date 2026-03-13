# 项目概览
- 目标：构建一个基于 MQTT 的 Windows 桌面工具，把小爱同学语音指令映射为本机白名单动作。
- 当前技术栈：Python 3.8+、PySide6、paho-mqtt、pytest。
- 代码结构：`src/xiaoai_desktop/` 下包含配置存储、动作执行、MQTT 监听、托盘 GUI、自启动；`tests/` 存放基础单元测试；根目录保留原始 `mqttClient.py` 作为参考原型。
- 运行入口：`python3 -m xiaoai_desktop`。
- 配置文件：默认保存在 Windows 的 `%APPDATA%/XiaoAiDesktop/config.json`，非 Windows 使用 `~/.xiaoai-desktop/config.json`。