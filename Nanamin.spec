# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('venv/lib/python3.13/site-packages/PyQt6/Qt6/plugins/platforms', 'PyQt6/Qt6/plugins/platforms'),
        ('venv/lib/python3.13/site-packages/PyQt6/Qt6/plugins/styles', 'PyQt6/Qt6/plugins/styles'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    argv_emulation=True,
    target_arch=None,
    icon='src/assets/nanamin_icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
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
    bundle_identifier='hr.crisp.nanamin',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
        'CFBundleDisplayName': 'Nanamin',
        'CFBundleName': 'Nanamin',
        'CFBundleGetInfoString': 'Manga & Comic Optimizer',
        'CFBundleIdentifier': 'hr.crisp.nanamin',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHumanReadableCopyright': '© 2024 Martin Crisp',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleEventsUsageDescription': 'This app needs to access files to optimize them.',
        'NSDesktopFolderUsageDescription': 'This app needs to access files to optimize them.',
        'NSDocumentsFolderUsageDescription': 'This app needs to access files to optimize them.',
        'NSDownloadsFolderUsageDescription': 'This app needs to access files to optimize them.',
    },
) 