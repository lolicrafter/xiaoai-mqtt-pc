# Agent Handover

本文档记录当前项目已经验证过的做法、踩坑点和推荐实现方式，供后续 agent 直接读取。

## 项目目标

- 使用小爱同学 / 米家 App 通过巴法云 MQTT 控制电脑动作。
- 桌面程序为本地 PySide6 GUI。
- 当前模型固定为巴法云窗帘设备 `A009`。
- 电脑端收到 `A009` 的消息后，按映射执行动作。

## 当前控制模型

程序固定监听：

- Topic / 设备 ID：`A009`

消息语义：

- `on`
- `off`
- `on#<percent>`

GUI 中的“窗帘映射”页负责配置：

- `on -> 动作`
- `off -> 动作`
- `on#百分比 -> 动作`

未配置的百分比消息只记日志，不执行。

## 当前动作类型

程序保留动作库，映射层只负责把窗帘消息绑定到动作。

已支持动作：

- 打开软件
- 运行脚本
- 切换显示器
- 组合动作（顺序执行多个步骤）

推荐原则：

- 能直接调用命令时，不要退化成快捷键。
- 快捷键仅作为无法直接调用命令时的备选方案。

## 巴法云连接要求

GUI 的 MQTT 页中：

- `主机`：通常为 `bemfa.com`
- `端口`：通常为 `9501`
- `巴法云私钥`：填巴法云私钥

注意：

- 之前 GUI 中这个字段叫 `Client ID`，现已改为 `巴法云私钥`。
- 保存时会自动执行 `strip()` 去掉首尾空格。
- 若 MQTT 返回 `状态码 5`，优先怀疑私钥错误或认证失败。

## 已验证的 GUI / 程序行为

- 程序首次启动默认不再最小化到托盘。
- 托盘图标已改为有效图标。
- 托盘单击和双击都可尝试唤起窗口。
- 收到 MQTT 消息时：
  - 终端会打印：
    - `[MQTT] topic=A009 payload=...`
  - GUI 日志页会新增一条：
    - 动作：`MQTT`
    - 消息：`收到 MQTT 消息`
- 若未匹配到动作，GUI 日志会记录 `WARNING`。

## 配置文件位置

macOS 默认配置文件：

```text
/Users/<用户名>/.xiaoai-desktop/config.json
```

Windows 默认配置文件：

```text
C:\Users\<用户名>\AppData\Roaming\XiaoAiDesktop\config.json
```

当前配置模型包含：

- `mqtt`
- `app`
- `curtain`
- `actions`

其中 `curtain` 结构示例：

```json
{
  "topic": "A009",
  "on_action_id": "xxx",
  "off_action_id": "yyy",
  "percent_actions": {
    "60": "zzz"
  }
}
```

## macOS 已验证经验

### 1. 系统应用不要直接执行包内二进制

例如不要直接执行：

```text
/System/Applications/Notes.app/Contents/MacOS/Notes
```

这可能触发：

- `Code Signature Invalid`
- `Launch Constraint Violation`

更稳的方式：

- 使用“运行脚本”动作
- 脚本内调用：

```bash
open -a "Notes"
```

### 2. 发送快捷键脚本已验证

已提供脚本：

- [send_hotkey.sh](/Users/zhuwei/code/zhuwei/temp/scripts/send_hotkey.sh)

默认行为：

- 发送 `Command+Shift+3`

也支持传参：

```bash
./scripts/send_hotkey.sh n command
./scripts/send_hotkey.sh q control shift
```

### 3. macOS 辅助功能权限必需

使用 `osascript` / `System Events` 发送按键时，必须给宿主程序授予“辅助功能”权限，例如：

- Terminal
- PyCharm

否则会报：

```text
osascript 不允许发送按键 (1002)
```

### 4. 普通应用快捷键可触发，系统级截图快捷键不稳定

已验证：

- `Command+N` 可触发
- `Command+Shift+3` 这种系统截图快捷键不一定能通过模拟按键稳定触发

结论：

- 应用级快捷键：可以走 `send_hotkey.sh`
- 系统级动作：优先直接调用系统命令

例如截图应直接使用：

```bash
screencapture -x ~/Desktop/test-shot.png
```

## Windows 推荐经验

### 1. 打开软件

Windows 下通常直接填 `.exe` 绝对路径即可。

例如：

```text
C:\Program Files\SomeApp\SomeApp.exe
```

### 2. MonitorSwitcher 优先走命令，不优先走热键

推荐优先验证命令行形式，而不是先依赖 `Ctrl+Shift+Q/W`。

候选形式：

```bat
"C:\Program Files\MonitorSwitcher\MonitorSwitcher.exe" -load:"C:\Users\用户名\AppData\Roaming\MonitorSwitcher\Profiles\TV.xml"
```

如果命令行可用，则应优先：

- `on -> 切到电视 profile`
- `off -> 切到显示器 profile`

只有在命令行方式不可用或不稳定时，才退回热键方案。

### 3. 发送快捷键优先用 AutoHotkey

如果 Windows 下必须发快捷键，优先使用 `AutoHotkey`。

推荐原则：

- 打开软件：直接 `.exe`
- 切换显示器：直接 `MonitorSwitcher.exe + profile`
- 发快捷键：运行 `.ahk`
- 多步骤：组合动作

示例：

```ahk
Send "^+q"
```

## GitHub 打包

仓库已加入 Release 自动打包工作流：

- [release-build.yml](/Users/zhuwei/code/zhuwei/temp/.github/workflows/release-build.yml)

当前策略：

- 仅在 GitHub Release `published` 时触发
- 先跑 `pytest -q`
- 测试通过后在 Windows runner 上打包
- 压缩为 zip
- 自动上传到当前 Release 页面

## 已知设计结论

- 当前产品模型已经不再是“任意 topic + alias 的通用 MQTT 动作中心”。
- 当前明确收敛为“固定 `A009` 窗帘映射 + 动作库”。
- 后续 agent 若继续演进，应优先围绕这个模型，而不是回退到通用 topic 配置。

## 后续改动建议

若继续开发，优先级建议如下：

1. 把“切换显示器”动作改成明确支持 `MonitorSwitcher -load:profile.xml`
2. 为 Windows 增加 AutoHotkey 示例脚本模板
3. 补 `.gitignore`
4. 增加配置导入导出
5. 增加窗帘映射导出清单按钮
