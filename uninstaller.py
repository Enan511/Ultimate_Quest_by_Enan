import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot, QObject, QThread
from PySide6.QtGui import QIcon

try:
    import winreg
except ImportError:
    winreg = None


DARK_THEME = '''
QWidget {
    background-color: #121212;
    color: #ffffff;
    font-family: "Segoe UI";
    font-size: 13px;
}
QFrame#card {
    background-color: #1a1a1a;
    border-radius: 8px;
    border: 1px solid #2a2a2a;
}
QPushButton {
    background-color: #1f538d;
    border: none;
    border-radius: 4px;
    padding: 9px 18px;
    color: #ffffff;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #296cbd;
}
QPushButton#uninstall_btn {
    background-color: #d93838;
    font-size: 14px;
}
QPushButton#uninstall_btn:hover {
    background-color: #e54a4a;
}
QProgressBar {
    background-color: #222222;
    border: 1px solid #333333;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #d93838;
    border-radius: 4px;
}
'''


def get_self_exe_path():
    try:
        return os.path.normpath(os.path.abspath(sys.executable))
    except Exception:
        return os.path.normpath(os.path.abspath(__file__))


def get_install_folder():
    return os.path.dirname(get_self_exe_path())


def get_desktop_path():
    if winreg:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            expanded = os.path.expandvars(val)
            if os.path.exists(expanded):
                return expanded
        except Exception:
            pass
    fallback = os.path.join(os.path.expanduser("~"), "Desktop")
    return fallback


def get_start_menu_path():
    if winreg:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Programs")
            winreg.CloseKey(key)
            expanded = os.path.expandvars(val)
            if os.path.exists(expanded):
                return expanded
        except Exception:
            pass
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")
    return None


def schedule_folder_deletion(folder_path, exe_path):
    '''Compile a C# deleter binary (or batch file) to delete the install folder and self-delete.'''
    try:
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or os.path.expanduser("~")
        pid = os.getpid()

        cs_path = os.path.join(temp_dir, f"_ueq_uninst_{pid}.cs")
        deleter_exe = os.path.join(temp_dir, f"uninst_deleter_{pid}.exe")

        cs_lines = [
            "using System;",
            "using System.IO;",
            "using System.Threading;",
            "using System.Diagnostics;",
            "",
            "class UninstDeleter {",
            "    static void Main(string[] args) {",
            "        if (args.Length < 2) return;",
            "        string folderPath = args[0];",
            "        string uninstExe = args[1];",
            "",
            "        for (int i = 0; i < 30; i++) {",
            "            try {",
            "                if (File.Exists(uninstExe)) {",
            "                    File.Delete(uninstExe);",
            "                }",
            "                break;",
            "            } catch {",
            "                Thread.Sleep(1000);",
            "            }",
            "        }",
            "",
            "        for (int i = 0; i < 30; i++) {",
            "            try {",
            "                if (Directory.Exists(folderPath)) {",
            "                    Directory.Delete(folderPath, true);",
            "                }",
            "                break;",
            "            } catch {",
            "                Thread.Sleep(1000);",
            "            }",
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
        with open(cs_path, "w", encoding="utf-8") as f:
            f.write("\n".join(cs_lines))

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
                [deleter_exe, folder_path, exe_path],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                close_fds=True
            )
            try:
                os.remove(cs_path)
            except Exception:
                pass
        else:
            bat_path = os.path.join(temp_dir, f"_ueq_uninst_{pid}.bat")
            bat_lines = [
                "@echo off",
                ":loop",
                f'del /f /q "{exe_path}" >nul 2>&1',
                f'if exist "{exe_path}" (',
                "  timeout /t 1 /nobreak >nul",
                "  goto loop",
                ")",
                f'rmdir /s /q "{folder_path}" >nul 2>&1',
                'del /f /q "%~f0"'
            ]
            with open(bat_path, "w", newline='') as f:
                f.write("\r\n".join(bat_lines) + "\r\n")
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                close_fds=True
            )
    except Exception as e:
        print(f"Error scheduling deletion: {e}")


class UninstallerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UEQ Uninstaller — Ultimate Quest")
        self.resize(550, 320)
        self.setMinimumSize(500, 280)

        self.folder_to_delete = get_install_folder()
        self.exe_to_delete = get_self_exe_path()
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Uninstall Ultimate Quest")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff6b6b;")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        msg = QLabel("Are you sure you want to completely remove Ultimate Quest and all its components?")
        msg.setStyleSheet("font-size: 13px; color: #ffffff;")
        msg.setWordWrap(True)
        card_layout.addWidget(msg)

        path_lbl = QLabel(f"Installation Folder:\n{self.folder_to_delete}")
        path_lbl.setStyleSheet("font-size: 12px; color: #888888;")
        path_lbl.setWordWrap(True)
        card_layout.addWidget(path_lbl)

        layout.addWidget(card)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(self.cancel_btn)

        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setObjectName("uninstall_btn")
        self.uninstall_btn.clicked.connect(self.start_uninstallation)
        btn_row.addWidget(self.uninstall_btn)

        layout.addLayout(btn_row)
        self.setCentralWidget(central)

    def start_uninstallation(self):
        # 1. Remove Desktop Shortcut
        desktop_lnk = os.path.join(get_desktop_path(), "Ultimate Quest.lnk")
        if os.path.exists(desktop_lnk):
            try:
                os.remove(desktop_lnk)
            except Exception:
                pass

        # 2. Remove Start Menu Shortcut
        start_menu_dir = get_start_menu_path()
        if start_menu_dir:
            start_lnk = os.path.join(start_menu_dir, "Ultimate Quest.lnk")
            if os.path.exists(start_lnk):
                try:
                    os.remove(start_lnk)
                except Exception:
                    pass

        # 3. Schedule self & folder deletion
        schedule_folder_deletion(self.folder_to_delete, self.exe_to_delete)

        QMessageBox.information(
            self,
            "Uninstall Complete",
            "Ultimate Quest has been uninstalled. The remaining files will be removed momentarily."
        )
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    win = UninstallerApp()
    win.show()
    sys.exit(app.exec())
