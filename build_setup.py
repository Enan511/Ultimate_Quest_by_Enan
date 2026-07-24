"""
build_setup.py - Packaging script for the Setup Installer.

Compiles setup_installer.py into a single, standalone executable (Ultimate_Quest_Setup.exe),
bundling Ultimate_Quest_Folder and icon assets.
"""

import sys
import os
import subprocess
import shutil

MAIN_ICON_SRC = r"D:\ML practice\Icons\UQ.ico"


def run_pyinstaller(cmd, step_name):
    """Run a PyInstaller command with error handling."""
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"\nERROR during {step_name}: PyInstaller not found.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR during {step_name}: PyInstaller exited with code {e.returncode}.")
        sys.exit(1)


def main():
    print("Building Ultimate Quest Setup Executable...")

    if not os.path.exists("Ultimate_Quest_Folder"):
        print("ERROR: Ultimate_Quest_Folder not found. Run UltimateQuestbyENAN.py first!")
        sys.exit(1)

    os.makedirs("icons", exist_ok=True)
    if os.path.exists(MAIN_ICON_SRC):
        shutil.copy(MAIN_ICON_SRC, os.path.join("icons", "UQ.ico"))
        shutil.copy(MAIN_ICON_SRC, "uq.ico")

    main_icon_arg = []
    if os.path.exists("uq.ico"):
        main_icon_arg = ["--icon", os.path.abspath("uq.ico")]

    add_data_args = [
        "--add-data", f"Ultimate_Quest_Folder{os.pathsep}Ultimate_Quest_Folder",
        "--add-data", f"icons{os.pathsep}icons"
    ]

    exclusions = [
        "--exclude-module", "numpy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "tkinter"
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
    ] + main_icon_arg + add_data_args + [
        "--name", "Ultimate_Quest_Setup"
    ] + exclusions + ["setup_installer.py"]

    run_pyinstaller(cmd, "Setup compilation")

    if os.path.exists(os.path.join("dist", "Ultimate_Quest_Setup.exe")):
        shutil.copy(os.path.join("dist", "Ultimate_Quest_Setup.exe"), "Ultimate_Quest_Setup.exe")
        print("\nSUCCESS! Standalone Setup Executable created: Ultimate_Quest_Setup.exe")

    for file in ["uq.ico", "setup_installer.spec", "Ultimate_Quest_Setup.spec"]:
        if os.path.exists(file):
            os.remove(file)
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)


if __name__ == "__main__":
    main()
