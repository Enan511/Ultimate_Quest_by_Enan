"""
build_setup.py - Packaging script for the Setup Installer.

Compiles setup_installer.py into a single, standalone executable (Ultimate_Quest_Setup.exe),
bundling Ultimate_Quest_Folder and icon assets.
"""

import sys
import os
import subprocess
import shutil

from build_support import pyinstaller_environment, qt_runtime_files, runtime_binary_args

MAIN_ICON_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "UQ.ico")


def run_pyinstaller(cmd, step_name):
    """Run a PyInstaller command with error handling."""
    try:
        subprocess.run(cmd, check=True, env=pyinstaller_environment())
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

    main_icon_arg = ["--icon", MAIN_ICON_SRC]

    add_data_args = [
        "--add-data", f"Ultimate_Quest_Folder{os.pathsep}Ultimate_Quest_Folder",
        "--add-data", f"{MAIN_ICON_SRC}{os.pathsep}icons"
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
    ] + runtime_binary_args(qt_runtime_files()) + exclusions + ["setup_installer.py"]

    run_pyinstaller(cmd, "Setup compilation")

    if os.path.exists(os.path.join("dist", "Ultimate_Quest_Setup.exe")):
        shutil.copy(os.path.join("dist", "Ultimate_Quest_Setup.exe"), "Ultimate_Quest_Setup.exe")
        print("\nSUCCESS! Standalone Setup Executable created: Ultimate_Quest_Setup.exe")

    for file in ["setup_installer.spec", "Ultimate_Quest_Setup.spec"]:
        if os.path.exists(file):
            os.remove(file)
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)


if __name__ == "__main__":
    main()
