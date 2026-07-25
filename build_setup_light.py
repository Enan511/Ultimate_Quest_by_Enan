"""
build_setup_light.py - Solid LZMA2 Packaging script for UQ Setup_Light.exe.

1. Packs Ultimate_Quest_Folder into a solid LZMA2 archive (payload.tar.xz).
2. Compiles setup_installer_light.py bundling payload.tar.xz.
3. Produces a highly compact UQ Setup_Light.exe (~30 MB).
"""

import sys
import os
import tarfile
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
    print("Building Solid LZMA2 Lightweight Setup Executable (UQ Setup_Light.exe)...")

    if not os.path.exists("Ultimate_Quest_Folder"):
        print("ERROR: Ultimate_Quest_Folder not found. Run UltimateQuestbyENAN.py first!")
        sys.exit(1)

    # 1. Prepare staging folder without UEQ Uninstaller.exe
    light_folder = "Ultimate_Quest_Folder_Light"
    if os.path.exists(light_folder):
        shutil.rmtree(light_folder)

    shutil.copytree("Ultimate_Quest_Folder", light_folder)
    uninst_in_light = os.path.join(light_folder, "UEQ Uninstaller.exe")
    if os.path.exists(uninst_in_light):
        os.remove(uninst_in_light)

    # 2. Compress staging folder into solid LZMA2 archive
    print("Step 1: Creating solid LZMA2 payload archive (payload.tar.xz)...")
    payload_path = "payload.tar.xz"
    if os.path.exists(payload_path):
        os.remove(payload_path)

    with tarfile.open(payload_path, "w:xz", preset=9) as tar:
        tar.add(light_folder, arcname="Ultimate_Quest_Folder")

    payload_size_mb = os.path.getsize(payload_path) / (1024 * 1024)
    print(f"  Solid LZMA2 payload compressed size: {payload_size_mb:.2f} MB")

    # 3. Prepare icons
    os.makedirs("icons", exist_ok=True)
    if os.path.exists(MAIN_ICON_SRC):
        shutil.copy(MAIN_ICON_SRC, os.path.join("icons", "UQ.ico"))
        shutil.copy(MAIN_ICON_SRC, "uq.ico")

    main_icon_arg = []
    if os.path.exists("uq.ico"):
        main_icon_arg = ["--icon", os.path.abspath("uq.ico")]

    add_data_args = [
        "--add-data", f"{payload_path}{os.pathsep}.",
        "--add-data", f"icons{os.pathsep}icons"
    ]

    exclusions = [
        "--exclude-module", "PySide6",
        "--exclude-module", "shiboken6",
        "--exclude-module", "numpy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy"
    ]

    print("Step 2: Compiling UQ Setup_Light.exe with bundled LZMA2 payload...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
    ] + main_icon_arg + add_data_args + [
        "--name", "UQ Setup_Light"
    ] + exclusions + ["setup_installer_light.py"]

    run_pyinstaller(cmd, "Solid LZMA2 Setup compilation")

    out_exe = os.path.join("dist", "UQ Setup_Light.exe")
    if os.path.exists(out_exe):
        shutil.copy(out_exe, "UQ Setup_Light.exe")
        final_size_mb = os.path.getsize("UQ Setup_Light.exe") / (1024 * 1024)
        print(f"\nSUCCESS! Solid LZMA2 Setup Executable created: UQ Setup_Light.exe ({final_size_mb:.2f} MB)")

    # Cleanup temporary files
    for file in ["uq.ico", "payload.tar.xz", "setup_installer_light.spec", "UQ Setup_Light.spec"]:
        if os.path.exists(file):
            os.remove(file)
    for folder in ["build", "dist", light_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)


if __name__ == "__main__":
    main()
