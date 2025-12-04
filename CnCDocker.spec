# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for CnCDocker

a = Analysis(
    ['CnCDocker'],
    pathex=[],
    binaries=[],
    datas=[('Flags', 'Flags')],  # Bundle the Flags directory with the .exe
    hiddenimports=['requests', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CnCDocker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (tkinter GUI app)
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon path here if you have one
)
