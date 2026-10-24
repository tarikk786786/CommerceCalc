"""
Synchronize CommerceCalc distribution folder and update Windows shortcuts.
Ensures project encapsulation inside apps/CommerceCalc/ and creates shortcuts on:
1. Desktop (C:/Users/tarik/Desktop/CommerceCalc.lnk)
2. Home (C:/Users/tarik/CommerceCalc.lnk)
3. Start Menu Programs (AppData/Roaming/Microsoft/Windows/Start Menu/Programs/CommerceCalc.lnk)
"""

import shutil
from pathlib import Path
import win32com.client

PROJECT_DIR = Path("C:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc").resolve()
ROOT_DIST = Path("C:/Users/tarik/Desktop/MY TOOLS/dist/CommerceCalc").resolve()
APP_DIST = PROJECT_DIR / "dist" / "CommerceCalc"

# 1. Sync ROOT_DIST to APP_DIST if ROOT_DIST is newer
if ROOT_DIST.exists():
    APP_DIST.parent.mkdir(parents=True, exist_ok=True)
    if APP_DIST.exists():
        shutil.rmtree(APP_DIST)
    shutil.copytree(ROOT_DIST, APP_DIST)
    print(f"Synced build from {ROOT_DIST} to {APP_DIST}")
    # Clean up loose dist in root to keep workspace clean
    shutil.rmtree(ROOT_DIST.parent)
    print("Cleaned root dist folder.")

EXE_PATH = APP_DIST / "CommerceCalc.exe"
assert EXE_PATH.exists(), f"Target executable not found at {EXE_PATH}"
print(f"Target executable confirmed: {EXE_PATH} ({EXE_PATH.stat().st_size / (1024*1024):.2f} MB)")

# 2. Update shortcuts
shell = win32com.client.Dispatch("WScript.Shell")
shortcut_destinations = [
    Path("C:/Users/tarik/Desktop/CommerceCalc.lnk"),
    Path("C:/Users/tarik/CommerceCalc.lnk"),
    Path(shell.SpecialFolders("Programs")) / "CommerceCalc.lnk",
]

icon_path = str(PROJECT_DIR / "assets" / "icon.ico")

for sc_path in shortcut_destinations:
    try:
        sc = shell.CreateShortcut(str(sc_path))
        sc.TargetPath = str(EXE_PATH)
        sc.WorkingDirectory = str(APP_DIST)
        sc.Description = "CommerceCalc — All-in-One E-Commerce Profit, Pricing & Google SEO Suite"
        if Path(icon_path).exists():
            sc.IconLocation = f"{icon_path},0"
        sc.Save()
        print(f"Successfully configured shortcut: {sc_path}")
    except Exception as e:
        print(f"Error creating shortcut {sc_path}: {e}")
