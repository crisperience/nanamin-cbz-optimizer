# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets', 'assets'),
        ('/opt/homebrew/share/qt/plugins/platforms/libqcocoa.dylib', 'platforms'),
        ('/opt/homebrew/share/qt/plugins/styles/libqmacstyle.dylib', 'styles'),
        ('/opt/homebrew/share/qt/plugins/imageformats', 'imageformats')
    ],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['qt_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Nanamin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity='Apple Development: martin.kajtazi95@gmail.com (3V3T4TQDVV)',
    entitlements_file='entitlements.plist',
    icon=['src/assets/nanamin_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nanamin',
)
app = BUNDLE(
    coll,
    name='Nanamin.app',
    icon='src/assets/nanamin_icon.icns',
    bundle_identifier='com.crisp.nanamin',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 Martin Kajtazi',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
    },
)
