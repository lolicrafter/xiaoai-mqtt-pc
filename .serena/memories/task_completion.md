# 完成任务后检查
- 运行 `./.venv/bin/pytest -q`，确保核心测试通过。
- 如有 Python 结构改动，再执行 `python3 -m compileall src tests`。
- 若涉及 GUI 行为，至少做一次手工启动验证：`./.venv/bin/python -m xiaoai_desktop`。
- 涉及开机自启或 MonitorSwitcher 时，需要在 Windows 环境做最终联调。 