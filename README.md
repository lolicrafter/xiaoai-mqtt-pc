# XiaoAi Desktop


[基于 MQTT 的 Windows 桌面工具，用于把小爱同学语音指令映射为本机动作。](https://zhuanlan.zhihu.com/p/707971163)

## 功能

- 本地桌面 GUI 管理 MQTT 连接、动作和日志
- 系统托盘常驻监听
- 白名单动作执行
- 支持打开软件、运行脚本、切换显示器、组合动作
- 支持开机自启

## 开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python3 -m xiaoai_desktop
```

## 当前界面能力

- 动作类型：打开软件、运行脚本、切换显示器、组合动作
- 组合动作：在 GUI 中从下拉框选择现有动作，按顺序加入步骤，并支持上移、下移、移除
- 日志：展示时间、级别、主题、载荷、动作与结果
- 系统：支持最小化到托盘与开机自启

## Windows 打包

Windows 下可直接运行：

```bat
scripts\build_windows.bat
```

打包脚本会：

- 创建项目本地 `.venv`
- 安装开发与打包依赖
- 调用 `PyInstaller`
- 输出到 `dist\XiaoAiDesktop`

如果你想手工打包：

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
.venv\Scripts\pyinstaller.exe packaging\xiaoai_desktop.spec --noconfirm --clean
```
