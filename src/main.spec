# -*- mode: python ; coding: utf-8 -*-

import os

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # Include FFmpeg binary
        (os.path.join(project_root, 'bin', 'ffmpeg.exe'), 'bin'),
        # Include Deno binary for JavaScript runtime
        (os.path.join(project_root, 'bin', 'deno.exe'), 'bin'),
    ],
    datas=[
        (os.path.join(project_root, 'assets', 'logo.ico'), 'assets'),
        (os.path.join(project_root, 'assets', 'logo.png'), 'assets'),
    ],
    hiddenimports=[
        'pystray._win32',  # Ensure Windows tray support is included
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MicroDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(project_root, 'assets', 'logo.ico')],
    version=None,
    uac_admin=False,
)
