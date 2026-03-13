# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
generated_dir = project_root / "build" / "macos"
icon_path = generated_dir / "app_icon.icns"

block_cipher = None

a = Analysis(
    [str(project_root / "src" / "bootstrap_app.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "裁剪的圆形图片.png"), "."),
        (str(project_root / "favicon.ico"), "."),
    ],
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="XiaoAiDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(icon_path) if icon_path.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="XiaoAiDesktop",
)
app = BUNDLE(
    coll,
    name="XiaoAiDesktop.app",
    icon=str(icon_path) if icon_path.exists() else None,
    bundle_identifier=None,
)
