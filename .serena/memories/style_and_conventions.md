# 风格约定
- 使用中文注释和中文界面文案。
- 核心数据结构采用 dataclass，动作类型使用 Enum。
- 桌面 GUI 与核心逻辑分层：`controller` 协调配置、日志、MQTT 和执行器；`main_window` 负责 UI。
- 动作执行只允许白名单动作类型，不直接暴露任意 shell 字符串执行。
- 先补可测试的核心模块，再接 GUI。