import sys
import os
import subprocess
import shutil

# False = Folder build with instant launch (recommended, 100% VirusTotal safe)
BUILD_SINGLE_FILE = False

RCEDIT_PATH = "rcedit.exe"

MAIN_ICON_SRC = r"D:\ML practice\Icons\UQ.ico"
STEAM_ICON_SRC = r"D:\ML practice\Icons\Steam.ico"
TIMER_ICONS = [
    r"D:\Icons\Jett.ico",
    r"D:\Icons\winking-face.ico",
    r"D:\Icons\Sekshy Jett.ico",
    r"D:\Icons\Ahri.ico"
]


def run_pyinstaller(cmd, step_name):
    """Run a PyInstaller command with error handling."""
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"\nERROR during {step_name}: PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR during {step_name}: PyInstaller exited with code {e.returncode}.")
        sys.exit(1)


def main():
    """Build the timer and Ultimate Quest executables."""
    print("Step 1: Generating the Dark-Mode Timer Script...")
    with open("timer_app.py", "w", encoding="utf-8") as f:
        f.write(TIMER_CODE)

    print("Step 2: Compiling Timer App...")
    run_pyinstaller(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
         "--exclude-module", "PySide6", "--exclude-module", "numpy",
         "--exclude-module", "matplotlib", "--exclude-module", "pandas",
         "--exclude-module", "scipy",
         "--name", "timer", "timer_app.py"],
        "Timer compilation"
    )

    print("Step 3: Moving timer.exe to working directory...")
    shutil.copy(os.path.join("dist", "timer.exe"), "timer.exe")

    print("Step 4: Preparing Icon Bundle...")
    os.makedirs("icons", exist_ok=True)
    for icon_src in TIMER_ICONS:
        if os.path.exists(icon_src):
            shutil.copy(icon_src, os.path.join("icons", os.path.basename(icon_src)))
    if os.path.exists(STEAM_ICON_SRC):
        shutil.copy(STEAM_ICON_SRC, os.path.join("icons", "Steam.ico"))
    if os.path.exists(MAIN_ICON_SRC):
        shutil.copy(MAIN_ICON_SRC, os.path.join("icons", "UQ.ico"))

    main_icon_arg = []
    if os.path.exists(MAIN_ICON_SRC):
        shutil.copy(MAIN_ICON_SRC, "uq.ico")
        main_icon_arg = ["--icon", os.path.abspath("uq.ico")]

    print("Step 5: Generating the Ultimate Quest Script...")
    with open("main_builder.py", "w", encoding="utf-8") as f:
        f.write(BUILDER_CODE)

    print("Step 6: Compiling Ultimate Quest App and Bundling Timer & Icons...")

    add_data_args = [
        "--add-data", f"timer.exe{os.pathsep}.",
        "--add-data", f"icons{os.pathsep}icons"
    ]

    rcedit_available = os.path.exists(RCEDIT_PATH)
    if rcedit_available:
        add_data_args += ["--add-data", f"{RCEDIT_PATH}{os.pathsep}."]
        print("  Found rcedit.exe - built games will also get a distinct Explorer icon.")

    exclusions = [
        "--exclude-module", "numpy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "tkinter"
    ]

    build_mode = "--onefile" if BUILD_SINGLE_FILE else "--onedir"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        build_mode,
        "--windowed",
    ] + main_icon_arg + add_data_args + [
        "--name", "Ultimate_Quest"
    ] + exclusions + ["main_builder.py"]

    run_pyinstaller(cmd, "Ultimate Quest compilation")

    print("Step 7: Moving and patching output executables...")

    if BUILD_SINGLE_FILE:
        shutil.copy(os.path.join("dist", "Ultimate_Quest.exe"), "Ultimate_Quest.exe")
    else:
        out_dir = "Ultimate_Quest_Folder"
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        shutil.move(os.path.join("dist", "Ultimate_Quest"), out_dir)

        if os.path.exists("uninstaller.py"):
            print("Step 6b: Compiling UEQ Uninstaller.exe...")
            run_pyinstaller(
                [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
                 "--name", "UEQ Uninstaller"] + main_icon_arg + exclusions + ["uninstaller.py"],
                "Uninstaller compilation"
            )
            uninst_dist = os.path.join("dist", "UEQ Uninstaller.exe")
            if os.path.exists(uninst_dist):
                shutil.copy(uninst_dist, os.path.join(out_dir, "UEQ Uninstaller.exe"))
                print("  Bundled UEQ Uninstaller.exe into Ultimate_Quest_Folder.")

        print(f"\nSUCCESS! Your app is inside the '{out_dir}' folder.")


    for file in ["timer_app.py", "main_builder.py", "timer.exe", "uq.ico", "timer.spec", "Ultimate_Quest.spec"]:
        if os.path.exists(file):
            os.remove(file)
    for folder in ["build", "dist", "__pycache__", "icons"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    if BUILD_SINGLE_FILE:
        print("\nSUCCESS! You can now use 'Ultimate_Quest.exe'.")


TIMER_CODE = r"""
import sys
import os
import json
import time
import random
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


def _get_save_folder():
    '''Return the local app data folder for UltimateQuest.'''
    appdata_dir = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    folder = os.path.join(appdata_dir, "UltimateQuest")
    os.makedirs(folder, exist_ok=True)
    return folder


SAVE_FOLDER = _get_save_folder()
RUNNING_TIMERS_FILE = os.path.join(SAVE_FOLDER, "running_timers.json")
SETTINGS_FILE = os.path.join(SAVE_FOLDER, "settings.json")


def _self_exe_path():
    '''Return the normalized absolute path of the running executable.'''
    try:
        return os.path.normpath(os.path.abspath(sys.executable))
    except Exception:
        return os.path.normpath(os.path.abspath(__file__))


def _self_display_name():
    '''Return the display name (stem) of the running executable.'''
    return Path(_self_exe_path()).stem


def _self_icon_path():
    '''Return the icon file path if it exists alongside the executable.'''
    p = Path(_self_exe_path())
    candidate = p.with_name(p.stem + "_icon.ico")
    return str(candidate) if candidate.exists() else None


def _get_manifest_path():
    '''Return the associated steam appmanifest path if passed or present.'''
    p = Path(_self_exe_path())
    candidate = p.with_name(p.stem + "_manifest.path")
    if candidate.exists():
        try:
            return candidate.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""


def load_settings():
    '''Load settings from disk.'''
    defaults = {"ask_on_manual_close": True}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_settings(settings):
    '''Save settings to disk.'''
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass


class TimerWindow:
    '''Lightweight Tkinter countdown timer window.'''

    def __init__(self, root):
        self.root = root
        display_name = _self_display_name()
        self.root.title(display_name)

        self.settings = load_settings()

        icon_path = _self_icon_path()
        if icon_path:
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.root.geometry("350x150")
        self.root.resizable(False, False)
        self.root.configure(bg="#121212")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - 350) // 2
        y = (screen_h - 150) // 2
        self.root.geometry(f"350x150+{x}+{y}")

        frame = tk.Frame(self.root, bg="#121212")
        frame.pack(expand=True, fill="both", padx=15, pady=15)

        self.lbl_status = tk.Label(
            frame,
            text=display_name,
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff",
            bg="#121212",
            wraplength=320,
            justify="center"
        )
        self.lbl_status.pack(pady=(5, 5))

        self.lbl_timer = tk.Label(
            frame,
            text="00:00",
            font=("Segoe UI", 28, "bold"),
            fg="#00ffcc",
            bg="#121212"
        )
        self.lbl_timer.pack(pady=(0, 2))

        self.var_ask_timer = tk.BooleanVar(value=self.settings.get("ask_on_manual_close", True))
        self.chk_timer = tk.Checkbutton(
            frame,
            text="Ask every time before closing",
            variable=self.var_ask_timer,
            command=self.on_toggle_timer_chk,
            font=("Segoe UI", 9),
            fg="#aaaaaa",
            bg="#121212",
            selectcolor="#222222",
            activebackground="#121212",
            activeforeground="#ffffff"
        )
        self.chk_timer.pack(pady=(2, 5))

        # Runtime set to 15 Min 30s to 16 Min (930s to 960s)
        self.total_seconds = random.randint(15 * 60 + 30, 16 * 60)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.update_timer_display()
        self._write_status(self.total_seconds)
        self.tick_timer()

    def on_toggle_timer_chk(self):
        '''Save setting when checkbox inside timer window is toggled.'''
        self.settings["ask_on_manual_close"] = self.var_ask_timer.get()
        save_settings(self.settings)

    def tick_timer(self):
        '''Tick the countdown by one second.'''
        if self.total_seconds <= 0:
            self._schedule_self_delete()
            self._clear_status()
            self.root.destroy()
            return
        self.total_seconds -= 1
        self.update_timer_display()
        self._write_status(self.total_seconds)
        self.root.after(1000, self.tick_timer)

    def update_timer_display(self):
        '''Update the timer label with MM:SS format.'''
        mins, secs = divmod(self.total_seconds, 60)
        self.lbl_timer.config(text=f"{mins:02d}:{secs:02d}")

    def _write_status(self, remaining_seconds):
        '''Write remaining seconds to the shared running_timers file.'''
        try:
            data = {}
            if os.path.exists(RUNNING_TIMERS_FILE):
                try:
                    with open(RUNNING_TIMERS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data[_self_exe_path()] = {"remaining_seconds": remaining_seconds, "updated": time.time()}
            tmp_path = RUNNING_TIMERS_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp_path, RUNNING_TIMERS_FILE)
        except Exception:
            pass

    def _clear_status(self):
        '''Remove this timer's entry from the shared running_timers file.'''
        try:
            if os.path.exists(RUNNING_TIMERS_FILE):
                with open(RUNNING_TIMERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data.pop(_self_exe_path(), None)
                tmp_path = RUNNING_TIMERS_FILE + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.replace(tmp_path, RUNNING_TIMERS_FILE)
        except Exception:
            pass

    def _schedule_self_delete(self):
        '''Dynamically compile a deleter.exe using C# csc.exe to handle cleanup.'''
        try:
            exe_path = _self_exe_path()
            folder = os.path.dirname(exe_path)
            icon_path = _self_icon_path() or ""
            manifest_path = _get_manifest_path()
            temp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or folder
            pid = os.getpid()

            cs_path = os.path.join(temp_dir, f"_uq_deleter_{pid}.cs")
            deleter_exe = os.path.join(temp_dir, f"deleter_{pid}.exe")

            cs_lines = [
                "using System;",
                "using System.IO;",
                "using System.Threading;",
                "using System.Diagnostics;",
                "",
                "class Deleter {",
                "    static void Main(string[] args) {",
                "        if (args.Length < 1) return;",
                "        string exePath = args[0];",
                "        string iconPath = args.Length > 1 ? args[1] : \"\";",
                "        string folderPath = args.Length > 2 ? args[2] : \"\";",
                "        string manifestPath = args.Length > 3 ? args[3] : \"\";",
                "",
                "        for (int i = 0; i < 30; i++) {",
                "            try {",
                "                if (File.Exists(exePath)) {",
                "                    File.Delete(exePath);",
                "                }",
                "                break;",
                "            } catch {",
                "                Thread.Sleep(1000);",
                "            }",
                "        }",
                "",
                "        if (!string.IsNullOrEmpty(iconPath) && File.Exists(iconPath)) {",
                "            try { File.Delete(iconPath); } catch {}",
                "        }",
                "",
                "        if (!string.IsNullOrEmpty(manifestPath) && File.Exists(manifestPath)) {",
                "            try { File.Delete(manifestPath); } catch {}",
                "        }",
                "",
                "        if (!string.IsNullOrEmpty(folderPath) && Directory.Exists(folderPath)) {",
                "            try { Directory.Delete(folderPath, true); } catch {}",
                "        }",
                "",
                "        try {",
                "            string selfPath = Process.GetCurrentProcess().MainModule.FileName;",
                "            ProcessStartInfo psi = new ProcessStartInfo();",
                "            psi.FileName = \"cmd.exe\";",
                "            psi.Arguments = \"/c choice /C Y /N /D Y /T 1 & del /f /q \\\"\" + selfPath + \"\\\"\";",
                "            psi.WindowStyle = ProcessWindowStyle.Hidden;",
                "            psi.CreateNoWindow = true;",
                "            Process.Start(psi);",
                "        } catch {}",
                "    }",
                "}"
            ]
            cs_code = "\n".join(cs_lines)
            with open(cs_path, "w", encoding="utf-8") as f:
                f.write(cs_code)

            csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
            if not os.path.exists(csc_path):
                csc_path = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"

            if os.path.exists(csc_path):
                subprocess.run(
                    [csc_path, "/target:winexe", "/nologo", f"/out:{deleter_exe}", cs_path],
                    creationflags=0x08000000,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000

            if os.path.exists(deleter_exe):
                subprocess.Popen(
                    [deleter_exe, exe_path, icon_path, folder, manifest_path],
                    creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                    close_fds=True
                )
                try:
                    os.remove(cs_path)
                except Exception:
                    pass
            else:
                bat_path = os.path.join(temp_dir, f"_uq_cleanup_{pid}.bat")
                bat_lines = [
                    "@echo off",
                    ":loop",
                    f'del /f /q "{exe_path}" >nul 2>&1',
                    f'if exist "{exe_path}" (',
                    "  timeout /t 1 /nobreak >nul",
                    "  goto loop",
                    ")",
                ]
                if icon_path:
                    bat_lines.append(f'del /f /q "{icon_path}" >nul 2>&1')
                if manifest_path:
                    bat_lines.append(f'del /f /q "{manifest_path}" >nul 2>&1')
                bat_lines += [
                    f'rmdir /s /q "{folder}" >nul 2>&1',
                    'del /f /q "%~f0"',
                ]
                with open(bat_path, "w", newline='') as f:
                    f.write("\r\n".join(bat_lines) + "\r\n")
                subprocess.Popen(
                    ["cmd.exe", "/c", bat_path],
                    creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                    close_fds=True
                )
        except Exception:
            pass

    def on_close(self):
        '''Handle manual window close event.'''
        self.settings = load_settings()
        ask_everytime = self.settings.get("ask_on_manual_close", True)

        if not ask_everytime:
            self._schedule_self_delete()
            self._clear_status()
            self.root.destroy()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm Exit")
        dialog.geometry("400x220")
        dialog.resizable(False, False)
        dialog.configure(bg="#1a1a1a")

        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        x = (screen_w - 400) // 2
        y = (screen_h - 220) // 2
        dialog.geometry(f"400x220+{x}+{y}")
        dialog.transient(self.root)
        dialog.grab_set()

        lbl = tk.Label(
            dialog,
            text="Do you want to delete game files and manifest upon closing?",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#1a1a1a",
            wraplength=360,
            justify="center"
        )
        lbl.pack(pady=(15, 10))

        var_dialog_ask = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            dialog,
            text="Ask every time before closing",
            variable=var_dialog_ask,
            font=("Segoe UI", 10),
            fg="#cccccc",
            bg="#1a1a1a",
            selectcolor="#2a2a2a",
            activebackground="#1a1a1a",
            activeforeground="#ffffff"
        )
        chk.pack(pady=(0, 15))

        btn_frame = tk.Frame(dialog, bg="#1a1a1a")
        btn_frame.pack(fill="x", padx=30, pady=(5, 15))

        def action_yes():
            ask_val = var_dialog_ask.get()
            self.settings["ask_on_manual_close"] = ask_val
            self.var_ask_timer.set(ask_val)
            save_settings(self.settings)
            dialog.destroy()
            self._schedule_self_delete()
            self._clear_status()
            self.root.destroy()

        def action_no():
            ask_val = var_dialog_ask.get()
            self.settings["ask_on_manual_close"] = ask_val
            self.var_ask_timer.set(ask_val)
            save_settings(self.settings)
            dialog.destroy()

        btn_yes = tk.Button(
            btn_frame, text="Yes", font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg="#1f8b4c", activebackground="#28a85a", bd=0, width=12, pady=6, command=action_yes
        )
        btn_yes.pack(side="left", expand=True, padx=8)

        btn_no = tk.Button(
            btn_frame, text="No", font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg="#d93838", activebackground="#e54a4a", bd=0, width=12, pady=6, command=action_no
        )
        btn_no.pack(side="right", expand=True, padx=8)

        self.root.wait_window(dialog)


if __name__ == '__main__':
    root = tk.Tk()
    app = TimerWindow(root)
    root.mainloop()
"""

BUILDER_CODE = r"""
import sys
import os
import shutil
import subprocess
import threading
import psutil
import json
import time
import random
import struct
import requests
import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QLabel, QTextEdit, QLineEdit, QScrollArea,
    QMessageBox, QDialog, QInputDialog, QMenu, QFrame, QSizePolicy, QStyle,
    QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject
from PySide6.QtGui import QCursor, QFont, QAction, QPainter, QColor, QIcon

try:
    import winreg as _winreg
except ImportError:
    _winreg = None

appdata_dir = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
SAVE_FOLDER = os.path.join(appdata_dir, "UltimateQuest")
os.makedirs(SAVE_FOLDER, exist_ok=True)

HISTORY_FILE = os.path.join(SAVE_FOLDER, "history.json")
SETTINGS_FILE = os.path.join(SAVE_FOLDER, "settings.json")
RUNNING_TIMERS_FILE = os.path.join(SAVE_FOLDER, "running_timers.json")

GIST_RAW_URL = "https://gist.githubusercontent.com/Enan511/680cf54a3f323ab3739fb12bc65639a3/raw/Ultimate_quests.txt"
STEAMCMD_API_URL = "https://cmd.steamcmd.net/v1/info"
STEAM_STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"

USE_RCEDIT = True

DARK_THEME = '''
QWidget {
    background-color: #121212;
    color: #ffffff;
    font-family: "Segoe UI";
    font-size: 13px;
}
QFrame {
    border: none;
}
QLineEdit, QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}
QLineEdit:hover, QTextEdit:hover {
    border: 1px solid #555555;
    background-color: #222222;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #1f538d;
}
QPushButton {
    background-color: #1f538d;
    border: none;
    border-radius: 4px;
    padding: 8px 15px;
    color: #ffffff;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #296cbd;
}
QPushButton:pressed {
    background-color: #17406a;
}
QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}
QCheckBox {
    spacing: 5px;
}
QScrollArea {
    border: 1px solid #2b2b2b;
    background-color: #181818;
    border-radius: 6px;
}
QScrollBar:vertical {
    border: none;
    background: #181818;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #333333;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #555555;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QLabel {
    background: transparent;
}
'''

STYLE_ADD_BTN = '''
    QPushButton {
        background-color: #2b2b2b;
        border: none;
        border-radius: 4px;
        padding: 8px 15px;
        color: #ffffff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
    }
    QPushButton:pressed {
        background-color: #222222;
    }
'''
STYLE_BUILD_BTN = '''
    QPushButton {
        background-color: #1f8b4c;
        border: none;
        border-radius: 4px;
        padding: 8px 15px;
        color: #ffffff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #28a85a;
    }
    QPushButton:pressed {
        background-color: #176b3a;
    }
'''
STYLE_RERUN_BTN = '''
    QPushButton {
        background-color: #1f538d;
        border: none;
        border-radius: 4px;
        padding: 8px 15px;
        color: #ffffff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #296cbd;
    }
    QPushButton:pressed {
        background-color: #17406a;
    }
'''
STYLE_DELETE_BTN = '''
    QPushButton {
        background-color: #d93838;
        border: none;
        border-radius: 4px;
        padding: 8px 15px;
        color: #ffffff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #e54a4a;
    }
    QPushButton:pressed {
        background-color: #b52d2d;
    }
'''
STYLE_DISABLED_BTN = '''
    QPushButton {
        background-color: #555555;
        color: #888888;
        border: none;
        border-radius: 4px;
        padding: 8px 15px;
        font-weight: bold;
    }
'''
STYLE_GAME_ROW = '''
    QFrame {
        background-color: #202020;
        border-radius: 4px;
        margin: 1px;
    }
    QFrame:hover {
        background-color: #2a2a2a;
        border: 1px solid #3a3a3a;
    }
'''


def resource_path(relative_path):
    '''Get path to a resource.'''
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_exe_self_dir():
    '''Return directory of running executable.'''
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resolve_path(path_str):
    '''Resolve path relative to executable dir if not absolute.'''
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(get_exe_self_dir()) / p
    return str(p)


def truncate_path(path_str, max_chars=60):
    '''Truncate path string.'''
    if len(path_str) <= max_chars:
        return path_str
    parts = Path(path_str).parts
    if len(parts) <= 3:
        return path_str[:max_chars] + "..."
    head = str(Path(parts[0]) / parts[1])
    tail = str(Path(parts[-2]) / parts[-1])
    sep = "\\" if "\\" in path_str else "/"
    truncated = f"{head}{sep}...{sep}{tail}"
    if len(truncated) <= max_chars:
        return truncated
    return f"...{sep}{parts[-2]}{sep}{parts[-1]}"


def normalize_path_key(path):
    '''Normalize path key.'''
    return os.path.normpath(path).lower()


def read_running_timers():
    '''Read shared running_timers.json file.'''
    try:
        if os.path.exists(RUNNING_TIMERS_FILE):
            with open(RUNNING_TIMERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def write_running_timers(data):
    '''Write timer data to shared running_timers.json file.'''
    try:
        tmp_path = RUNNING_TIMERS_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_path, RUNNING_TIMERS_FILE)
    except Exception:
        pass


def build_random_icon_file(out_ico_path):
    '''Pick a random icon from bundled icons directory.'''
    try:
        icons_dir = resource_path("icons")
        if os.path.exists(icons_dir):
            icon_files = [
                os.path.join(icons_dir, f) for f in os.listdir(icons_dir)
                if f.lower().endswith(".ico") and f.lower() not in ("uq.ico", "steam.ico")
            ]
            if icon_files:
                chosen = random.choice(icon_files)
                shutil.copy(chosen, out_ico_path)
                return os.path.exists(out_ico_path) and os.path.getsize(out_ico_path) > 0
    except Exception as e:
        print(f"Error selecting icon: {e}")
    return False


# ── Steam Helpers ──────────────────────────────────────────────────────────

def get_steam_path() -> Path | None:
    '''Read Steam path from Windows registry.'''
    if sys.platform != 'win32' or _winreg is None:
        return None
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        val, _ = _winreg.QueryValueEx(key, "SteamPath")
        _winreg.CloseKey(key)
        p = Path(val)
        return p if p.exists() else None
    except Exception:
        fallback = Path(r"C:\Program Files (x86)\Steam")
        return fallback if fallback.exists() else None


def get_steam_user_id() -> str:
    '''Read active Steam user 64-bit ID.'''
    if sys.platform != 'win32' or _winreg is None:
        return "0"
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess")
        val, _ = _winreg.QueryValueEx(key, "ActiveUser")
        _winreg.CloseKey(key)
        return str(int(val) + 76561197960265728)
    except Exception:
        return "0"


def fetch_steam_app_info(appid: int) -> dict | None:
    '''Fetch app details from SteamCMD API.'''
    try:
        resp = requests.get(f"{STEAMCMD_API_URL}/{appid}", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        app_data = data.get("data", {}).get(str(appid), {})
        common = app_data.get("common", {})
        config_data = app_data.get("config", {})

        name = common.get("name", f"App {appid}")
        installdir = config_data.get("installdir", name)

        exe = None
        launch = config_data.get("launch", {})
        for k in sorted(launch.keys()):
            entry = launch[k]
            oslist = entry.get("config", {}).get("oslist", "windows")
            if "windows" in oslist or oslist == "":
                candidate = entry.get("executable", "")
                if candidate.endswith(".exe"):
                    exe = candidate.replace("\\", "/").split("/")[-1]
                    break
        if not exe:
            exe = installdir.split("/")[-1] + ".exe"
            if not exe.endswith(".exe"):
                exe += ".exe"

        depot_id = next(
            (k for k, v in app_data.get("depots", {}).items() if k.isdigit() and isinstance(v, dict)),
            None
        )
        return {"appid": appid, "name": name, "installdir": installdir, "executable": exe, "depot_id": depot_id}
    except Exception as e:
        print(f"SteamCMD API error: {e}")
        return None


def search_steam_store(query: str) -> list:
    '''Search Steam Store for games.'''
    try:
        resp = requests.get(
            STEAM_STORE_SEARCH_URL,
            params={"term": query, "l": "english", "cc": "US"},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception as e:
        print(f"Steam Store Search error: {e}")
        return []


def generate_appmanifest(appid, name, installdir, steam_path, depot_id=None):
    '''Generate appmanifest_<appid>.acf file in steamapps.'''
    depot_str = f'\n\t\t"{depot_id}"\n\t\t{{\n\t\t\t"manifest"\t\t"0"\n\t\t\t"size"\t\t"1073741824"\n\t\t\t"dlcappid"\t\t"0"\n\t\t}}' if depot_id else ""
    owner_id = get_steam_user_id()
    launcher_path = str(steam_path / "steam.exe").replace("/", "\\\\")

    acf_content = f'''"AppState"
{{
\t"appid"\t\t"{appid}"
\t"universe"\t\t"1"
\t"LauncherPath"\t\t"{launcher_path}"
\t"name"\t\t"{name}"
\t"StateFlags"\t\t"1026"
\t"installdir"\t\t"{installdir}"
\t"LastUpdated"\t\t"0"
\t"LastPlayed"\t\t"0"
\t"SizeOnDisk"\t\t"0"
\t"StagingSize"\t\t"1073741824"
\t"buildid"\t\t"0"
\t"LastOwner"\t\t"{owner_id}"
\t"DownloadType"\t\t"1"
\t"UpdateResult"\t\t"4"
\t"BytesToDownload"\t\t"1073741824"
\t"BytesDownloaded"\t\t"27262976"
\t"BytesToStage"\t\t"1073741824"
\t"BytesStaged"\t\t"27262976"
\t"TargetBuildID"\t\t"0"
\t"AutoUpdateBehavior"\t\t"0"
\t"AllowOtherDownloadsWhileRunning"\t\t"0"
\t"ScheduledAutoUpdate"\t\t"0"
\t"InstalledDepots"
\t{{
\t}}
\t"StagedDepots"
\t{{{depot_str}
\t}}
\t"UserConfig"
\t{{
\t}}
\t"MountedConfig"
\t{{
\t}}
}}
'''
    acf_path = steam_path / "steamapps" / f"appmanifest_{appid}.acf"
    try:
        acf_path.parent.mkdir(parents=True, exist_ok=True)
        with open(acf_path, "w", encoding="utf-8") as f:
            f.write(acf_content)
        return str(acf_path)
    except Exception as e:
        print(f"Failed to generate manifest: {e}")
        return None


class MultilinePlaceholderTextEdit(QTextEdit):
    '''QTextEdit with placeholder support.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._placeholder_text = ""

    def setPlaceholderText(self, text):
        self._placeholder_text = text
        self.viewport().update()

    def placeholderText(self):
        return self._placeholder_text

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.toPlainText() and self._placeholder_text:
            painter = QPainter(self.viewport())
            painter.setPen(QColor("#7a7a7a"))
            rect = self.viewport().rect().adjusted(4, 4, -4, -4)
            painter.setFont(self.font())
            painter.drawText(rect, int(Qt.TextWordWrap), self._placeholder_text)
            painter.end()


class WorkerSignals(QObject):
    '''Signals for background worker threads.'''
    gist_check_complete = Signal(list)
    gist_check_empty = Signal()
    gist_check_error = Signal(str)
    steam_search_complete = Signal(list)
    build_complete_trigger = Signal()


class ExeBuilderApp(QMainWindow):
    '''Main application window.'''

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Quest")
        self.resize(900, 750)
        self.setMinimumSize(700, 500)

        self.history = []
        self.ui_items = {}
        self.currently_building = set()
        self._data_lock = threading.RLock()
        self._running_exes_cache = set()
        self._running_exes_cache_time = 0.0
        self._last_known_existence = {}

        self.current_mode = "standard"  # "standard" or "steam"
        self.selected_steam_game = None

        self.signals = WorkerSignals()
        self.signals.gist_check_complete.connect(self.handle_new_quests)
        self.signals.gist_check_empty.connect(self.handle_empty_quests)
        self.signals.gist_check_error.connect(self.handle_gist_error)
        self.signals.steam_search_complete.connect(self.handle_steam_results)
        self.signals.build_complete_trigger.connect(self.refresh_lists)

        self.settings = self.load_settings()
        self.setup_ui()
        self.load_history()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_running_processes)
        self.poll_timer.start(2000)

    def load_settings(self):
        '''Load settings from disk.'''
        default_settings = {
            "always_ask_for_new_quests": True,
            "last_successful_check_timestamp": None,
            "deleted_paths": []
        }
        with self._data_lock:
            if os.path.exists(SETTINGS_FILE):
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                        for key in default_settings:
                            if key not in settings:
                                settings[key] = default_settings[key]
                        return settings
                except Exception as e:
                    print(f"Failed to load settings: {e}")
        return default_settings

    def save_settings(self):
        '''Persist settings to disk.'''
        with self._data_lock:
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.settings, f, indent=4)
            except Exception as e:
                print(f"Failed to save settings: {e}")

    @staticmethod
    def _scroll_height_for_rows(count, max_rows=5):
        rows = max(1, min(count, max_rows))
        return 53 * rows + 7

    def _compute_scroll_heights(self, built_count, unbuilt_count):
        built_rows = max(1, min(built_count, 3))
        unbuilt_max = max(3, 6 - built_rows)
        unbuilt_rows = max(1, min(unbuilt_count, unbuilt_max))
        return 53 * built_rows + 7, 53 * unbuilt_rows + 7

    def setup_ui(self):
        '''Build main UI with QStackedWidget for Standard/Steam modes.'''
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(20, 20, 20, 20)
        central_layout.setSpacing(10)

        # ── Top Bar ──
        top_bar = QHBoxLayout()

        self.check_quests_btn = QPushButton("Check for New Quests")
        self.check_quests_btn.setFixedHeight(35)
        self.check_quests_btn.setStyleSheet(STYLE_RERUN_BTN)
        self.check_quests_btn.setShortcut("Ctrl+N")
        self.check_quests_btn.clicked.connect(self.start_gist_check_thread)
        top_bar.addWidget(self.check_quests_btn)

        shortcut_icon = QLabel("!")
        shortcut_icon.setFixedSize(18, 18)
        shortcut_icon.setAlignment(Qt.AlignCenter)
        shortcut_icon.setStyleSheet(
            "background-color: #ffcc00; color: #121212; font-weight: bold; "
            "border-radius: 9px; font-size: 12px;"
        )
        top_bar.addWidget(shortcut_icon)

        shortcut_label = QLabel("Shortcut: Ctrl+N")
        shortcut_label.setStyleSheet("font-size: 12px; color: #aaaaaa; background: transparent;")
        top_bar.addWidget(shortcut_label)

        self.chk_always_ask = QCheckBox("Ask before adding")
        self.chk_always_ask.setChecked(self.settings["always_ask_for_new_quests"])
        self.chk_always_ask.stateChanged.connect(self.toggle_always_ask)
        top_bar.addWidget(self.chk_always_ask)

        self.lbl_last_updated = QLabel("Last Checked: Never")
        top_bar.addWidget(self.lbl_last_updated)
        self.update_last_checked_label()

        top_bar.addStretch()

        # Steam Mode Toggle Button on Top Right
        steam_icon_path = resource_path("icons/Steam.ico")
        self.steam_mode_btn = QPushButton("Steam Mode 🎮")
        if os.path.exists(steam_icon_path):
            self.steam_mode_btn.setIcon(QIcon(steam_icon_path))
        self.steam_mode_btn.setFixedHeight(35)
        self.steam_mode_btn.setStyleSheet(STYLE_RERUN_BTN)
        self.steam_mode_btn.clicked.connect(self.toggle_mode)
        top_bar.addWidget(self.steam_mode_btn)

        central_layout.addLayout(top_bar)

        # ── Stacked Input Frame (Morphing Card) ──
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 6px;")
        input_card_layout = QVBoxLayout(input_frame)
        input_card_layout.setContentsMargins(15, 15, 15, 15)

        self.stacked_widget = QStackedWidget()

        # ── Page 0: Standard Mode ──
        std_page = QWidget()
        std_layout = QVBoxLayout(std_page)
        std_layout.setContentsMargins(0, 0, 0, 0)

        lbl_instructions = QLabel("Add Games to List (Format: Game Name on line 1, Path on line 2):")
        lbl_instructions.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent;")
        std_layout.addWidget(lbl_instructions)

        self.bulk_entry = MultilinePlaceholderTextEdit()
        self.bulk_entry.setFixedHeight(90)
        self.bulk_entry.setPlaceholderText("Once Human\nOnce Human/OnceHuman.exe")
        std_layout.addWidget(self.bulk_entry)

        std_btn_row = QHBoxLayout()
        std_btn_row.addStretch()

        self.add_btn = QPushButton("Add to Game List")
        self.add_btn.setFixedHeight(35)
        self.add_btn.setStyleSheet(STYLE_ADD_BTN)
        self.add_btn.clicked.connect(lambda: self.add_bulk_games(trigger_build=False))
        std_btn_row.addWidget(self.add_btn)

        self.build_now_std_btn = QPushButton("Build Now")
        self.build_now_std_btn.setFixedHeight(35)
        self.build_now_std_btn.setStyleSheet(STYLE_BUILD_BTN)
        self.build_now_std_btn.clicked.connect(self.build_now_action)
        std_btn_row.addWidget(self.build_now_std_btn)

        std_layout.addLayout(std_btn_row)
        self.stacked_widget.addWidget(std_page)

        # ── Page 1: Steam Mode ──
        steam_page = QWidget()
        steam_layout = QVBoxLayout(steam_page)
        steam_layout.setContentsMargins(0, 0, 0, 0)

        lbl_steam_title = QLabel("🎮 Steam Quest Mode — Search Steam Store:")
        lbl_steam_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffcc; background: transparent;")
        steam_layout.addWidget(lbl_steam_title)

        steam_search_row = QHBoxLayout()
        self.steam_search_entry = QLineEdit()
        self.steam_search_entry.setPlaceholderText("Search Steam Game (e.g. Toxic Commando Demo, Marathon)...")
        self.steam_search_entry.setFixedHeight(35)
        self.steam_search_entry.returnPressed.connect(self.search_steam_action)
        steam_search_row.addWidget(self.steam_search_entry)

        self.steam_search_btn = QPushButton("Search Steam")
        self.steam_search_btn.setFixedHeight(35)
        self.steam_search_btn.setStyleSheet(STYLE_RERUN_BTN)
        self.steam_search_btn.clicked.connect(self.search_steam_action)
        steam_search_row.addWidget(self.steam_search_btn)
        steam_layout.addLayout(steam_search_row)

        self.lbl_steam_result = QLabel("Search for a Steam game to locate its AppID and installation path.")
        self.lbl_steam_result.setStyleSheet("font-size: 12px; color: #aaaaaa; background: transparent; padding: 4px;")
        self.lbl_steam_result.setWordWrap(True)
        steam_layout.addWidget(self.lbl_steam_result)

        steam_btn_row = QHBoxLayout()
        steam_btn_row.addStretch()

        self.build_now_steam_btn = QPushButton("Build Now")
        self.build_now_steam_btn.setFixedHeight(35)
        self.build_now_steam_btn.setStyleSheet(STYLE_DISABLED_BTN)
        self.build_now_steam_btn.setEnabled(False)
        self.build_now_steam_btn.clicked.connect(self.build_steam_action)
        steam_btn_row.addWidget(self.build_now_steam_btn)

        steam_layout.addLayout(steam_btn_row)
        self.stacked_widget.addWidget(steam_page)

        input_card_layout.addWidget(self.stacked_widget)
        central_layout.addWidget(input_frame)

        # ── Search Filter Row ──
        search_row = QHBoxLayout()
        search_row.addStretch()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search by Game Name...")
        self.search_entry.setFixedWidth(300)
        self.search_entry.setFixedHeight(35)
        self.search_entry.textChanged.connect(self.refresh_lists)
        search_row.addWidget(self.search_entry)
        central_layout.addLayout(search_row)

        # ── Created Executable History List ──
        self.lbl_built = QLabel("Created Executable History")
        self.lbl_built.setStyleSheet("font-size: 15px; font-weight: bold; color: #00ffcc;")
        central_layout.addWidget(self.lbl_built)

        self.built_scroll = QScrollArea()
        self.built_scroll_widget = QWidget()
        self.built_scroll_layout = QVBoxLayout(self.built_scroll_widget)
        self.built_scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.built_scroll_layout.setSpacing(5)
        self.built_scroll_widget.setStyleSheet("background-color: #181818;")
        self.built_scroll.setWidgetResizable(True)
        self.built_scroll.setWidget(self.built_scroll_widget)
        self.built_scroll.setFixedHeight(self._scroll_height_for_rows(1, max_rows=3))
        central_layout.addWidget(self.built_scroll)

        # ── Game List (Unbuilt) ──
        self.lbl_unbuilt = QLabel("Game List")
        self.lbl_unbuilt.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffcc00;")
        central_layout.addWidget(self.lbl_unbuilt)

        self.unbuilt_scroll = QScrollArea()
        self.unbuilt_scroll_widget = QWidget()
        self.unbuilt_scroll_layout = QVBoxLayout(self.unbuilt_scroll_widget)
        self.unbuilt_scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.unbuilt_scroll_layout.setSpacing(5)
        self.unbuilt_scroll_widget.setStyleSheet("background-color: #181818;")
        self.unbuilt_scroll.setWidgetResizable(True)
        self.unbuilt_scroll.setWidget(self.unbuilt_scroll_widget)
        self.unbuilt_scroll.setFixedHeight(self._scroll_height_for_rows(5, max_rows=5))
        central_layout.addWidget(self.unbuilt_scroll)

        central_layout.addStretch()
        self.setCentralWidget(central_widget)

    def toggle_mode(self):
        '''Toggle between Standard Mode and Steam Mode pages.'''
        if self.current_mode == "standard":
            self.current_mode = "steam"
            self.stacked_widget.setCurrentIndex(1)
            self.steam_mode_btn.setText("Standard Mode 📝")
        else:
            self.current_mode = "standard"
            self.stacked_widget.setCurrentIndex(0)
            self.steam_mode_btn.setText("Steam Mode 🎮")

    def search_steam_action(self):
        '''Trigger background search for Steam game.'''
        query = self.steam_search_entry.text().strip()
        if not query:
            return
        self.steam_search_btn.setEnabled(False)
        self.steam_search_btn.setText("Searching...")
        self.lbl_steam_result.setStyleSheet("font-size: 12px; color: #ffcc00; background: transparent;")
        self.lbl_steam_result.setText("Searching Steam Store...")
        self.selected_steam_game = None
        self.build_now_steam_btn.setEnabled(False)
        self.build_now_steam_btn.setStyleSheet(STYLE_DISABLED_BTN)

        thread = threading.Thread(target=self.bg_steam_search, args=(query,))
        thread.daemon = True
        thread.start()

    def bg_steam_search(self, query):
        '''Background thread for searching Steam.'''
        items = search_steam_store(query)
        self.signals.steam_search_complete.emit(items)

    @Slot(list)
    def handle_steam_results(self, items):
        '''Handle Steam search results.'''
        self.steam_search_btn.setEnabled(True)
        self.steam_search_btn.setText("Search Steam")

        if not items:
            self.lbl_steam_result.setStyleSheet("font-size: 12px; color: #ff4d4d; background: transparent;")
            self.lbl_steam_result.setText("🔴 Game not found on Steam. Check spelling or try adding 'Demo' to your query.")
            self.build_now_steam_btn.setEnabled(False)
            self.build_now_steam_btn.setStyleSheet(STYLE_DISABLED_BTN)
            self.selected_steam_game = None
            return

        first = items[0]
        appid = first.get("id")
        store_name = first.get("name", "Unknown Game")

        info = fetch_steam_app_info(appid)
        if not info:
            info = {
                "appid": appid,
                "name": store_name,
                "installdir": store_name.replace(" ", ""),
                "executable": store_name.replace(" ", "") + ".exe",
                "depot_id": None
            }

        steam_path = get_steam_path()
        if not steam_path:
            target_rel = f"Steam/steamapps/common/{info['installdir']}/{info['executable']}"
        else:
            target_rel = str(steam_path / "steamapps" / "common" / info['installdir'] / info['executable'])

        info["target_rel"] = target_rel
        self.selected_steam_game = info

        self.lbl_steam_result.setStyleSheet("font-size: 12px; color: #00ffcc; background: transparent;")
        self.lbl_steam_result.setText(
            f"🟢 Found: {info['name']} (AppID: {info['appid']})\n"
            f"Target Path: {info['target_rel']}"
        )

        self.build_now_steam_btn.setEnabled(True)
        self.build_now_steam_btn.setStyleSheet(STYLE_BUILD_BTN)

    def build_steam_action(self):
        '''Build the currently selected Steam game.'''
        if not self.selected_steam_game:
            QMessageBox.warning(self, "No Game to Build", "No game to build. Please search and select a valid Steam game first.")
            return

        info = self.selected_steam_game
        game_name = info["name"]
        exe_path = info["target_rel"]
        appid = info["appid"]
        installdir = info["installdir"]

        steam_path = get_steam_path()
        manifest_path = None
        if steam_path:
            manifest_path = generate_appmanifest(appid, game_name, installdir, steam_path, info.get("depot_id"))

        # Add to history
        with self._data_lock:
            key = normalize_path_key(exe_path)
            existing = {normalize_path_key(item["exe_path"]) for item in self.history}
            if key not in existing:
                self.history.append({
                    "exe_path": exe_path,
                    "root_dir": os.path.dirname(exe_path),
                    "game_name": game_name,
                    "ever_built": False,
                    "manifest_path": manifest_path
                })
        self.save_history()

        self.build_item_with_manifest(exe_path, manifest_path)

    def build_item_with_manifest(self, exe_path, manifest_path=None):
        '''Build item passing optional manifest path.'''
        self.currently_building.add(exe_path)
        self.refresh_lists()
        thread = threading.Thread(target=self.build_single_manifest_wrapper, args=(exe_path, manifest_path))
        thread.daemon = True
        thread.start()

    def build_single_manifest_wrapper(self, exe_path, manifest_path):
        self.build_exe_logic_manifest(exe_path, manifest_path)
        self.currently_building.discard(exe_path)
        self.signals.build_complete_trigger.emit()

    def build_exe_logic_manifest(self, full_path_str, manifest_path=None):
        '''Core build logic supporting steam manifest file creation.'''
        try:
            original_path_str = full_path_str
            resolved_path_str = resolve_path(full_path_str)
            target_file = Path(resolved_path_str)
            target_dir = target_file.parent
            exe_name = target_file.name

            target_dir.mkdir(parents=True, exist_ok=True)

            timer_exe_src = resource_path("timer.exe")
            full_exe_path = str(target_dir / exe_name)

            if not os.path.exists(timer_exe_src):
                raise FileNotFoundError("Bundled timer.exe not found!")

            shutil.copy(timer_exe_src, full_exe_path)

            icon_path = str(target_dir / (target_file.stem + "_icon.ico"))
            icon_built = build_random_icon_file(icon_path)

            if manifest_path:
                manifest_ref = str(target_dir / (target_file.stem + "_manifest.path"))
                with open(manifest_ref, "w", encoding="utf-8") as f:
                    f.write(manifest_path)


            with self._data_lock:
                for item in self.history:
                    if item["exe_path"] == original_path_str:
                        item["root_dir"] = str(target_dir)
                        item["ever_built"] = True
                        break
            self.save_history()

            if os.path.exists(full_exe_path):
                subprocess.Popen([full_exe_path])

        except Exception as e:
            err_msg = str(e)
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to build: {err_msg}"))

    def toggle_always_ask(self, state):
        self.settings["always_ask_for_new_quests"] = (state == 2)
        self.save_settings()

    def update_last_checked_label(self):
        timestamp_str = self.settings.get("last_successful_check_timestamp")
        if timestamp_str:
            last_checked = datetime.datetime.fromisoformat(timestamp_str)
            self.lbl_last_updated.setText(f"Last Checked: {last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.lbl_last_updated.setText("Last Checked: Never")

    def load_history(self):
        with self._data_lock:
            if os.path.exists(HISTORY_FILE):
                try:
                    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                        self.history = json.load(f)
                except Exception as e:
                    print(f"Failed to load history: {e}")
        self.refresh_lists()

    def save_history(self):
        with self._data_lock:
            try:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, indent=4)
            except Exception as e:
                print(f"Failed to save history: {e}")

    def start_gist_check_thread(self):
        self.check_quests_btn.setEnabled(False)
        self.check_quests_btn.setText("Checking...")
        thread = threading.Thread(target=self.check_for_new_quests)
        thread.daemon = True
        thread.start()

    def check_for_new_quests(self):
        try:
            response = requests.get(GIST_RAW_URL, timeout=10)
            response.raise_for_status()
            pending_quests = self.parse_gist_content(response.text)

            self.settings["last_successful_check_timestamp"] = datetime.datetime.now().isoformat()
            self.save_settings()

            if pending_quests:
                self.signals.gist_check_complete.emit(pending_quests)
            else:
                self.signals.gist_check_empty.emit()
        except Exception as e:
            self.signals.gist_check_error.emit(str(e))

    def parse_gist_content(self, content):
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        parsed_quests = []
        i = 0
        while i < len(lines):
            if i + 1 >= len(lines):
                break
            g_name = lines[i]
            e_path = lines[i + 1].strip('"').strip("'")
            if g_name and e_path.lower().endswith(".exe"):
                parsed_quests.append({"game_name": g_name, "exe_path": os.path.normpath(e_path)})
            i += 2

        with self._data_lock:
            existing_keys = {normalize_path_key(item["exe_path"]) for item in self.history}
        return [q for q in parsed_quests if normalize_path_key(q["exe_path"]) not in existing_keys]

    @Slot(list)
    def handle_new_quests(self, pending_quests):
        self.check_quests_btn.setEnabled(True)
        self.check_quests_btn.setText("Check for New Quests")
        self.update_last_checked_label()

        if not self.settings["always_ask_for_new_quests"]:
            truly_new_quests = [q for q in pending_quests if q["exe_path"] not in self.settings.get("deleted_paths", [])]
            if truly_new_quests:
                self.add_quests_to_history(truly_new_quests)
                QMessageBox.information(self, "New Quests Added", f"Automatically added {len(truly_new_quests)} new quest(s).")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Review New Quests")
        dialog.resize(600, 450)
        dialog_layout = QVBoxLayout(dialog)

        lbl = QLabel("Review available quests:")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        dialog_layout.addWidget(lbl)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignTop)

        checkboxes = {}
        for quest in pending_quests:
            exe_path = quest['exe_path']
            is_deleted = exe_path in self.settings.get("deleted_paths", [])
            chk = QCheckBox(f"[{quest['game_name']}] - {exe_path}")
            chk.setChecked(not is_deleted)
            scroll_layout.addWidget(chk)
            checkboxes[exe_path] = (chk, quest)

        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        dialog_layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Selected")
        add_btn.setStyleSheet(STYLE_BUILD_BTN)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(STYLE_DISABLED_BTN)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        dialog_layout.addLayout(btn_row)

        def add_action():
            quests_to_add = []
            for path, (chk, quest) in checkboxes.items():
                if chk.isChecked():
                    quests_to_add.append(quest)
            if quests_to_add:
                self.add_quests_to_history(quests_to_add)
            dialog.accept()

        add_btn.clicked.connect(add_action)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    @Slot()
    def handle_empty_quests(self):
        self.check_quests_btn.setEnabled(True)
        self.check_quests_btn.setText("Check for New Quests")
        self.update_last_checked_label()
        QMessageBox.information(self, "No New Quests", "You are fully up to date!")

    @Slot(str)
    def handle_gist_error(self, err_msg):
        self.check_quests_btn.setEnabled(True)
        self.check_quests_btn.setText("Check for New Quests")
        QMessageBox.critical(self, "Error", err_msg)

    def add_quests_to_history(self, quests):
        with self._data_lock:
            existing_keys = {normalize_path_key(item["exe_path"]) for item in self.history}
            for quest in quests:
                raw_path = quest['exe_path']
                key = normalize_path_key(raw_path)
                if raw_path.lower().endswith(".exe") and key not in existing_keys:
                    self.history.append({
                        "exe_path": raw_path,
                        "root_dir": None,
                        "game_name": quest['game_name'],
                        "ever_built": False
                    })
                    existing_keys.add(key)
        self.save_history()
        self.refresh_lists()

    def add_bulk_games(self, trigger_build=False):
        text = self.bulk_entry.toPlainText().strip()
        if not text:
            return []

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        added_paths = []
        valid_input = False
        skipped_messages = []

        i = 0
        while i < len(lines):
            if i + 1 >= len(lines):
                skipped_messages.append(f"'{lines[i]}' has no path on the line below it - skipped.")
                break
            g_name = lines[i].strip()
            e_path = lines[i + 1].strip('"').strip("'").strip()
            i += 2

            if not g_name or not e_path.lower().endswith(".exe"):
                continue

            e_path = os.path.normpath(e_path)
            valid_input = True

            with self._data_lock:
                existing_keys = {normalize_path_key(item["exe_path"]) for item in self.history}
                key = normalize_path_key(e_path)
                if key not in existing_keys:
                    self.history.append({
                        "exe_path": e_path,
                        "root_dir": None,
                        "game_name": g_name,
                        "ever_built": False
                    })
                    added_paths.append(e_path)
                elif trigger_build:
                    if not os.path.exists(resolve_path(e_path)):
                        added_paths.append(e_path)

        if valid_input:
            self.save_history()
            self.refresh_lists()
            self.bulk_entry.clear()

        return added_paths

    def build_now_action(self):
        paths_to_build = self.add_bulk_games(trigger_build=True)
        if paths_to_build:
            for p in paths_to_build:
                self.currently_building.add(p)
            self.refresh_lists()
            thread = threading.Thread(target=self.build_multiple_exes, args=(paths_to_build,))
            thread.daemon = True
            thread.start()

    def build_multiple_exes(self, paths):
        for path in paths:
            self.build_exe_logic_manifest(path)
            self.currently_building.discard(path)
            self.signals.build_complete_trigger.emit()

    def build_item(self, exe_path):
        self.currently_building.add(exe_path)
        self.refresh_lists()
        thread = threading.Thread(target=self.build_single_wrapper, args=(exe_path,))
        thread.daemon = True
        thread.start()

    def build_single_wrapper(self, exe_path):
        self.build_exe_logic_manifest(exe_path)
        self.currently_building.discard(exe_path)
        self.signals.build_complete_trigger.emit()

    def rerun_item(self, exe_path):
        resolved = resolve_path(exe_path)
        if os.path.exists(resolved):
            try:
                subprocess.Popen([resolved])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not launch: {e}")

    def delete_tracked_item(self, exe_path):
        with self._data_lock:
            root_dir = None
            manifest_path = None
            for item in self.history:
                if item["exe_path"] == exe_path:
                    root_dir = item.get("root_dir")
                    manifest_path = item.get("manifest_path")
                    break

        resolved_exe = resolve_path(exe_path)
        try:
            if manifest_path and os.path.exists(manifest_path):
                try:
                    os.remove(manifest_path)
                except Exception:
                    pass
            if root_dir and os.path.exists(root_dir):
                if os.path.isdir(root_dir):
                    shutil.rmtree(root_dir)
                else:
                    os.remove(root_dir)
            elif os.path.exists(resolved_exe):
                os.remove(resolved_exe)
            self.refresh_lists()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not delete files: {e}")

    def get_running_exes(self, max_age=1.0):
        now = time.monotonic()
        if (now - self._running_exes_cache_time) < max_age:
            return self._running_exes_cache

        running = set()
        for p in psutil.process_iter(['exe']):
            try:
                exe_path = p.info.get('exe')
                if exe_path:
                    running.add(os.path.normpath(os.path.abspath(exe_path)))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self._running_exes_cache = running
        self._running_exes_cache_time = now
        return running

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_lists(self):
        search_query = self.search_entry.text().lower().strip()
        with self._data_lock:
            self.history.sort(key=lambda x: x.get("game_name", "").lower())
            history_snapshot = list(self.history)

        self.clear_layout(self.built_scroll_layout)
        self.clear_layout(self.unbuilt_scroll_layout)
        self.ui_items.clear()

        running_exes = self.get_running_exes()
        built_count = 0
        unbuilt_count = 0

        for item in history_snapshot:
            exe_path = item["exe_path"]
            g_name = item.get("game_name", "Unknown Game")
            ever_built = item.get("ever_built", False)

            if search_query and search_query not in g_name.lower():
                continue

            resolved_exe = resolve_path(exe_path)
            exists = os.path.exists(resolved_exe)
            parent_layout = self.built_scroll_layout if exists else self.unbuilt_scroll_layout
            if exists:
                built_count += 1
            else:
                unbuilt_count += 1

            item_frame = QFrame()
            item_frame.setStyleSheet(STYLE_GAME_ROW)
            frame_layout = QHBoxLayout(item_frame)
            frame_layout.setContentsMargins(10, 6, 10, 6)

            display_path = truncate_path(exe_path)
            lbl = QLabel(f"[{g_name}]  -  {display_path}")
            lbl.setStyleSheet("font-size: 13px; font-weight: normal; background: transparent;")
            frame_layout.addWidget(lbl, stretch=1)

            item_frame.setContextMenuPolicy(Qt.CustomContextMenu)
            item_frame.customContextMenuRequested.connect(lambda pos, p=exe_path: self.show_context_menu(pos, p))

            if exists:
                lbl_time = QLabel("")
                lbl_time.setStyleSheet("font-size: 12px; font-weight: bold; color: #00ffcc; background: transparent;")
                lbl_time.setFixedWidth(55)
                lbl_time.setAlignment(Qt.AlignCenter)
                frame_layout.addWidget(lbl_time)

                btn_frame = QWidget()
                btn_frame.setStyleSheet("background: transparent;")
                btn_row = QHBoxLayout(btn_frame)
                btn_row.setContentsMargins(0, 0, 0, 0)
                btn_row.setSpacing(5)

                btn_rerun = QPushButton("Rerun")
                btn_rerun.setFixedWidth(80)
                btn_rerun.setStyleSheet(STYLE_RERUN_BTN)
                btn_rerun.clicked.connect(lambda checked=False, p=exe_path: self.rerun_item(p))
                btn_row.addWidget(btn_rerun)

                btn_del = QPushButton("Delete Path")
                btn_del.setFixedWidth(110)
                btn_del.setStyleSheet(STYLE_DELETE_BTN)
                btn_del.clicked.connect(lambda checked=False, p=exe_path: self.delete_tracked_item(p))
                btn_row.addWidget(btn_del)

                is_running = os.path.normpath(resolved_exe) in running_exes
                if is_running:
                    btn_del.setEnabled(False)
                    btn_del.setText("Running...")
                    btn_del.setStyleSheet(STYLE_DISABLED_BTN)
                    btn_rerun.setEnabled(False)
                    btn_rerun.setStyleSheet(STYLE_DISABLED_BTN)

                frame_layout.addWidget(btn_frame)
                self.ui_items[exe_path] = {
                    "btn_delete": btn_del,
                    "btn_rerun": btn_rerun,
                    "lbl_time": lbl_time,
                    "is_running": is_running,
                    "state": "built",
                    "game_name": g_name
                }
            else:
                if exe_path in self.currently_building:
                    btn_build = QPushButton("Building...")
                    btn_build.setFixedWidth(100)
                    btn_build.setEnabled(False)
                    btn_build.setStyleSheet(STYLE_DISABLED_BTN)
                else:
                    btn_build = QPushButton("Rebuild" if ever_built else "Build")
                    btn_build.setFixedWidth(100)
                    btn_build.setStyleSheet(STYLE_BUILD_BTN)
                    btn_build.clicked.connect(lambda checked=False, p=exe_path: self.build_item(p))
                frame_layout.addWidget(btn_build)

                self.ui_items[exe_path] = {
                    "btn_build": btn_build,
                    "is_running": False,
                    "state": "unbuilt",
                    "game_name": g_name
                }

            parent_layout.addWidget(item_frame)

        built_h, unbuilt_h = self._compute_scroll_heights(built_count, unbuilt_count)
        self.built_scroll.setFixedHeight(built_h)
        self.unbuilt_scroll.setFixedHeight(unbuilt_h)

    def show_context_menu(self, pos, exe_path):
        menu = QMenu(self)
        menu.setStyleSheet('''
            QMenu { background-color: #2b2b2b; color: white; border: 1px solid #555; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #1f538d; }
        ''')

        act_edit = QAction("Edit Game Name", self)
        act_edit.triggered.connect(lambda: self.edit_game_name(exe_path))
        menu.addAction(act_edit)

        act_copy = QAction("Copy Path", self)
        act_copy.triggered.connect(lambda: self.copy_path(exe_path))
        menu.addAction(act_copy)

        menu.addSeparator()

        act_del = QAction("Delete from History", self)
        act_del.triggered.connect(lambda: self.delete_from_history(exe_path))
        menu.addAction(act_del)

        menu.exec(QCursor.pos())

    def edit_game_name(self, exe_path):
        new_name, ok = QInputDialog.getText(self, "Edit Game Name", "Enter Game Name:")
        if ok and new_name.strip():
            with self._data_lock:
                for item in self.history:
                    if item["exe_path"] == exe_path:
                        item["game_name"] = new_name.strip()
                        break
            self.save_history()
            self.refresh_lists()

    def copy_path(self, exe_path):
        clipboard = QApplication.clipboard()
        clipboard.setText(exe_path)

    def delete_from_history(self, exe_path):
        resolved_exe = resolve_path(exe_path)
        if os.path.normpath(resolved_exe) in self.get_running_exes():
            QMessageBox.warning(self, "Game Running", "Game is currently running. Close the exe and retry.")
            return

        with self._data_lock:
            root_dir = None
            manifest_path = None
            for item in self.history:
                if item["exe_path"] == exe_path:
                    root_dir = item.get("root_dir")
                    manifest_path = item.get("manifest_path")
                    break

        try:
            if manifest_path and os.path.exists(manifest_path):
                try:
                    os.remove(manifest_path)
                except Exception:
                    pass
            if root_dir and os.path.exists(root_dir):
                if os.path.isdir(root_dir):
                    shutil.rmtree(root_dir)
                else:
                    os.remove(root_dir)
            elif os.path.exists(resolved_exe):
                os.remove(resolved_exe)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not delete files: {e}")

        with self._data_lock:
            self.history = [item for item in self.history if item["exe_path"] != exe_path]
        self.save_history()

        with self._data_lock:
            if exe_path not in self.settings.get("deleted_paths", []):
                if "deleted_paths" not in self.settings:
                    self.settings["deleted_paths"] = []
                self.settings["deleted_paths"].append(exe_path)
        self.save_settings()

        self.refresh_lists()

    def poll_running_processes(self):
        running_exes = self.get_running_exes()
        running_timers = read_running_timers()
        needs_refresh = False

        with self._data_lock:
            history_snapshot = list(self.history)

        current_existence = {}
        for item in history_snapshot:
            exe_path = item["exe_path"]
            exists_now = os.path.exists(resolve_path(exe_path))
            current_existence[exe_path] = exists_now
            if self._last_known_existence.get(exe_path) != exists_now:
                needs_refresh = True
        self._last_known_existence = current_existence

        if self.ui_items:
            for exe_path, data in list(self.ui_items.items()):
                resolved_exe = resolve_path(exe_path)
                exists_on_disk = os.path.exists(resolved_exe)
                is_built_state = (data["state"] == "built")

                if exists_on_disk != is_built_state or not exists_on_disk:
                    continue

                normalized_target = os.path.normpath(resolved_exe)
                is_running = normalized_target in running_exes

                if is_running and not data["is_running"]:
                    data["btn_delete"].setEnabled(False)
                    data["btn_delete"].setText("Running...")
                    data["btn_delete"].setStyleSheet(STYLE_DISABLED_BTN)
                    data["btn_rerun"].setEnabled(False)
                    data["btn_rerun"].setStyleSheet(STYLE_DISABLED_BTN)
                    data["is_running"] = True
                elif not is_running and data["is_running"]:
                    data["btn_delete"].setEnabled(True)
                    data["btn_delete"].setText("Delete Path")
                    data["btn_delete"].setStyleSheet(STYLE_DELETE_BTN)
                    data["btn_rerun"].setEnabled(True)
                    data["btn_rerun"].setStyleSheet(STYLE_RERUN_BTN)
                    data["is_running"] = False

                lbl_time = data.get("lbl_time")
                if lbl_time is not None:
                    info = running_timers.get(normalized_target) if is_running else None
                    if info and "remaining_seconds" in info:
                        secs = max(0, int(info["remaining_seconds"]))
                        mins, s = divmod(secs, 60)
                        lbl_time.setText(f"{mins:02d}:{s:02d}")
                    else:
                        lbl_time.setText("")

            if running_timers:
                still_valid = {k: v for k, v in running_timers.items() if k in running_exes}
                if len(still_valid) != len(running_timers):
                    write_running_timers(still_valid)

        if needs_refresh:
            self.refresh_lists()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    window = ExeBuilderApp()
    window.show()
    sys.exit(app.exec())
"""

if __name__ == "__main__":
    main()
