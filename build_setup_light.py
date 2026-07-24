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
    print("Building Lightweight Setup Executable (UQ Setup_Light.exe)...")

    if not os.path.exists("Ultimate_Quest_Folder"):
        print("ERROR: Ultimate_Quest_Folder not found. Run UltimateQuestbyENAN.py first!")
        sys.exit(1)

    # Prepare lightweight folder without UEQ Uninstaller.exe
    light_folder = "Ultimate_Quest_Folder_Light"
    if os.path.exists(light_folder):
        shutil.rmtree(light_folder)

    shutil.copytree("Ultimate_Quest_Folder", light_folder)
    uninst_in_light = os.path.join(light_folder, "UEQ Uninstaller.exe")
    if os.path.exists(uninst_in_light):
        os.remove(uninst_in_light)

    os.makedirs("icons", exist_ok=True)
    if os.path.exists(MAIN_ICON_SRC):
        shutil.copy(MAIN_ICON_SRC, os.path.join("icons", "UQ.ico"))
        shutil.copy(MAIN_ICON_SRC, "uq.ico")

    main_icon_arg = []
    if os.path.exists("uq.ico"):
        main_icon_arg = ["--icon", os.path.abspath("uq.ico")]

    add_data_args = [
        "--add-data", f"{light_folder}{os.pathsep}Ultimate_Quest_Folder",
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
        "--name", "UQ Setup_Light"
    ] + exclusions + ["setup_installer_light.py"]

    run_pyinstaller(cmd, "Lightweight Setup compilation")

    out_exe = os.path.join("dist", "UQ Setup_Light.exe")
    if os.path.exists(out_exe):
        shutil.copy(out_exe, "UQ Setup_Light.exe")
        print("\nSUCCESS! Standalone Lightweight Setup Executable created: UQ Setup_Light.exe")

    # Cleanup temporary staging directories
    for file in ["uq.ico", "setup_installer_light.spec", "UQ Setup_Light.spec"]:
        if os.path.exists(file):
            os.remove(file)
    for folder in ["build", "dist", light_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)


if __name__ == "__main__":
    main()
