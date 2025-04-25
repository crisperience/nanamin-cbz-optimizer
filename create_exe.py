import PyInstaller.__main__
import os
import shutil
from pathlib import Path
import sys
import plistlib

# Configuration
APP_NAME = "Nanamin"
VERSION = "0.1.0"
ICON_PATH = "src/assets/icon.png"
ASSETS_PATH = "src/assets"

# Check if running on Windows
IS_WINDOWS = sys.platform == "win32"

# Clean up previous builds
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# Base PyInstaller arguments
pyinstaller_args = [
    "src/main.py",
    "--name",
    APP_NAME,
    "--windowed",
    "--icon",
    ICON_PATH,
    "--add-data",
    f"{ASSETS_PATH}{os.pathsep}{os.path.basename(ASSETS_PATH)}",
    "--clean",
]

if IS_WINDOWS:
    # Create version info file for Windows
    version_info = f"""
    VSVersionInfo(
      ffi=FixedFileInfo(
        filevers=({VERSION.replace('.', ', ')}, 0),
        prodvers=({VERSION.replace('.', ', ')}, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
      ),
      kids=[
        StringFileInfo(
          [
          StringTable(
            u'040904B0',
            [StringStruct(u'CompanyName', u'Nanamin'),
            StringStruct(u'FileDescription', u'CBZ Optimizer'),
            StringStruct(u'FileVersion', u'{VERSION}'),
            StringStruct(u'InternalName', u'{APP_NAME}'),
            StringStruct(u'LegalCopyright', u'MIT License'),
            StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
            StringStruct(u'ProductName', u'Nanamin CBZ Optimizer'),
            StringStruct(u'ProductVersion', u'{VERSION}')])
          ]), 
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
      ]
    )
    """
    with open("version_info.txt", "w") as f:
        f.write(version_info)

    # Add Windows-specific arguments
    pyinstaller_args.extend(["--onefile", "--version-file", "version_info.txt"])
else:
    # macOS-specific arguments
    pyinstaller_args.extend(
        [
            "--onedir",
            "--osx-bundle-identifier",
            "com.crisperience.nanamin",
        ]
    )

# Create executable
PyInstaller.__main__.run(pyinstaller_args)

# Clean up temporary files
if os.path.exists("version_info.txt"):
    os.remove("version_info.txt")

if not IS_WINDOWS:
    # Update Info.plist for macOS
    info_plist_path = f"dist/{APP_NAME}.app/Contents/Info.plist"
    if os.path.exists(info_plist_path):
        with open(info_plist_path, "rb") as f:
            info_plist = plistlib.load(f)

        # Update the plist with additional keys
        info_plist.update(
            {
                "CFBundleShortVersionString": VERSION,
                "CFBundleVersion": VERSION,
                "LSMinimumSystemVersion": "10.13.0",
                "NSHighResolutionCapable": True,
                "NSRequiresAquaSystemAppearance": False,
                "CFBundleDisplayName": APP_NAME,
                "CFBundleIdentifier": "com.crisperience.nanamin",
                "CFBundlePackageType": "APPL",
                "LSApplicationCategoryType": "public.app-category.utilities",
            }
        )

        with open(info_plist_path, "wb") as f:
            plistlib.dump(info_plist, f)

if IS_WINDOWS:
    try:
        import winreg

        # Create file association registry entries
        def create_file_association():
            try:
                # Get the full path to the executable
                exe_path = os.path.abspath(f"dist/{APP_NAME}.exe")

                # Create registry entries for CBZ files
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER, f"Software\\Classes\\.cbz"
                ) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, f"{APP_NAME}.cbz")

                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{APP_NAME}.cbz"
                ) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, "CBZ File")
                    winreg.SetValueEx(
                        key, "FriendlyTypeName", 0, winreg.REG_SZ, "CBZ File"
                    )

                    with winreg.CreateKey(key, "DefaultIcon") as icon_key:
                        winreg.SetValue(icon_key, "", winreg.REG_SZ, f"{exe_path},0")

                    with winreg.CreateKey(key, "shell\\open\\command") as cmd_key:
                        winreg.SetValue(
                            cmd_key, "", winreg.REG_SZ, f'"{exe_path}" "%1"'
                        )

                print("File association created successfully!")
            except Exception as e:
                print(f"Warning: Could not create file association: {e}")
                print(
                    "You can still use the application, but file association won't be available."
                )

        # Create file association
        create_file_association()
        print(f"\nWindows executable created: dist/{APP_NAME}.exe")
        print("The executable is portable and can be run from any location")
        print("\nFile association has been set up automatically.")
        print("You can now right-click on CBZ files to use the application.")
    except ImportError:
        print(
            "Warning: Could not import winreg module. File association will not be available."
        )
else:
    print(f"\nmacOS application bundle created: dist/{APP_NAME}.app")
    print("You can now move the .app bundle to your Applications folder")
