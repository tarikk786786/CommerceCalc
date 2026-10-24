"""
Build standalone CommerceCalc.exe using PyInstaller.
Excludes unnecessary heavy packages (torch, scipy, matplotlib) for lightning fast, lean compilation.
"""

import PyInstaller.__main__
from pathlib import Path

app_dir = Path(__file__).parent.resolve()
icon_path = str(app_dir / "assets" / "app.ico")
main_script = str(app_dir / "main.py")

args = [
    main_script,
    "--name=CommerceCalc",
    "--windowed",
    "--noconsole",
    "--clean",
    "--noconfirm",
    f"--icon={icon_path}",
    f"--add-data={app_dir / 'assets'};assets",
    f"--add-data={app_dir / 'data'};data",
    f"--add-data={app_dir / 'src'};src",
    "--exclude-module=torch",
    "--exclude-module=torchvision",
    "--exclude-module=torchaudio",
    "--exclude-module=scipy",
    "--exclude-module=matplotlib",
    "--exclude-module=IPython",
    "--exclude-module=jupyter",
    "--exclude-module=notebook",
    "--exclude-module=tkinter",
    "--exclude-module=pytest",
    "--exclude-module=setuptools",
]

print("Starting optimized PyInstaller build for CommerceCalc.exe...")
PyInstaller.__main__.run(args)
print("Build complete!")
