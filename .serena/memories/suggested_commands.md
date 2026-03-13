# 常用命令
- 创建虚拟环境：`python3 -m venv .venv`
- 安装依赖：`./.venv/bin/pip install -e '.[dev]'`
- 运行测试：`./.venv/bin/pytest -q`
- 语法检查：`python3 -m compileall src tests`
- 启动程序：`./.venv/bin/python -m xiaoai_desktop`
- 最小化启动：`./.venv/bin/python -m xiaoai_desktop --minimized`
