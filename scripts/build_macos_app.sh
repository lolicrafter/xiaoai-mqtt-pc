#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PNG_ICON="$ROOT_DIR/裁剪的圆形图片.png"
BUILD_DIR="$ROOT_DIR/build/macos"
ICONSET_DIR="$BUILD_DIR/app_icon.iconset"
ICNS_ICON="$BUILD_DIR/app_icon.icns"

if [ ! -f "$PNG_ICON" ]; then
  echo "未找到图标文件：$PNG_ICON" >&2
  exit 1
fi

python3 -m venv .venv
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$ROOT_DIR/.venv/bin/pip" install -e ".[build]"

rm -rf "$ICONSET_DIR" "$ICNS_ICON"
mkdir -p "$ICONSET_DIR"

sips -z 16 16 "$PNG_ICON" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
sips -z 32 32 "$PNG_ICON" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
sips -z 32 32 "$PNG_ICON" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
sips -z 64 64 "$PNG_ICON" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
sips -z 128 128 "$PNG_ICON" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
sips -z 256 256 "$PNG_ICON" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
sips -z 256 256 "$PNG_ICON" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
sips -z 512 512 "$PNG_ICON" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
sips -z 512 512 "$PNG_ICON" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
cp "$PNG_ICON" "$ICONSET_DIR/icon_512x512@2x.png"

iconutil -c icns "$ICONSET_DIR" -o "$ICNS_ICON"

"$ROOT_DIR/.venv/bin/pyinstaller" "packaging/xiaoai_desktop_macos.spec" --noconfirm --clean

echo
echo "打包完成，产物目录：dist/XiaoAiDesktop.app"
