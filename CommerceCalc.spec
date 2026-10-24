# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/assets', 'assets'), ('C:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/data', 'data'), ('C:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/src', 'src')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'scipy', 'matplotlib', 'IPython', 'jupyter', 'notebook', 'tkinter', 'pytest', 'setuptools'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CommerceCalc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/assets/app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CommerceCalc',
)
