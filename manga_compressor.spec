# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/assets', 'assets')],  # Include assets directory
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,  # Optimize bytecode
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # This is the key change - don't include binaries in the exe
    name='Nanamin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/assets/icon.png',
)

# Create macOS .app bundle
app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Nanamin.app',
    icon='src/assets/icon.png',
    bundle_identifier='com.nanamin.cbzoptimizer',
    info_plist={
        'CFBundleName': 'Nanamin',
        'CFBundleDisplayName': 'Nanamin - CBZ Optimizer',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
        'LSEnvironment': {
            'PYTHONOPTIMIZE': '2',  # Optimize Python
            'PYTHONDONTWRITEBYTECODE': '1',  # Don't write .pyc files
        },
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
    },
) 