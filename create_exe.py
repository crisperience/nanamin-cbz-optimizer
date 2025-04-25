import PyInstaller.__main__
import os
import shutil
from pathlib import Path
import sys

# Configuration
APP_NAME = "Nanamin"
VERSION = "1.0.0"
ICON_PATH = "src/assets/icon.png"
ASSETS_PATH = "src/assets"

# Check if running on Windows
IS_WINDOWS = sys.platform == "win32"

# Clean up previous builds
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# Create version info file
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

# Create executable
PyInstaller.__main__.run(
    [
        "src/main.py",
        "--name",
        APP_NAME,
        "--onefile",
        "--windowed",
        "--icon",
        ICON_PATH,
        "--add-data",
        f"{ASSETS_PATH}{os.pathsep}{os.path.basename(ASSETS_PATH)}",
        "--version-file",
        "version_info.txt",
        "--clean",
    ]
)

# Clean up version info file
os.remove("version_info.txt")

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
    except ImportError:
        print(
            "Warning: Could not import winreg module. File association will not be available."
        )
else:
    print("Note: File association is only available on Windows.")

print(f"\nPortable Windows executable created: dist/{APP_NAME}.exe")
print("The executable is portable and can be run from any location")
if IS_WINDOWS:
    print("\nFile association has been set up automatically.")
    print("You can now right-click on CBZ files to use the application.")
