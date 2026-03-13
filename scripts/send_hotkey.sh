#!/bin/bash

set -euo pipefail

# 用法：
#   ./scripts/send_hotkey.sh
#   ./scripts/send_hotkey.sh 3 command shift
#   ./scripts/send_hotkey.sh q control shift
#
# 说明：
# - 默认发送 Command+Shift+3
# - 第一个参数是按键字符
# - 后续参数是修饰键，可选：command / control / option / shift
# - 运行前请确保 Terminal 或 Python 已获得“辅助功能”权限

KEY="${1:-3}"
shift || true

if [ "$#" -eq 0 ]; then
  MODIFIERS=("command" "shift")
else
  MODIFIERS=("$@")
fi

if [ "${#KEY}" -ne 1 ]; then
  echo "按键必须是单个字符，例如：3 / q / w" >&2
  exit 1
fi

MODIFIER_LIST=""
for modifier in "${MODIFIERS[@]}"; do
  case "$modifier" in
    command|control|option|shift)
      if [ -n "$MODIFIER_LIST" ]; then
        MODIFIER_LIST="$MODIFIER_LIST, "
      fi
      MODIFIER_LIST="${MODIFIER_LIST}${modifier} down"
      ;;
    *)
      echo "不支持的修饰键：$modifier" >&2
      exit 1
      ;;
  esac
done

osascript <<EOF
tell application "System Events"
    keystroke "$KEY" using {$MODIFIER_LIST}
end tell
EOF
