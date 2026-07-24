import sys
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QLabel, QLineEdit, QProgressBar, QFileDialog,
    QStackedWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QObject, QThread
from PySide6.QtGui import QIcon, QFont, QColor, QPainter

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
QLineEdit {
    background-color: #222222;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 8px;
    color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #00ffcc;
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
QPushButton:pressed {
    background-color: #17406a;
}
QPushButton#install_btn {
    background-color: #1f8b4c;
    font-size: 14px;
}
QPushButton#install_btn:hover {
    background-color: #28a85a;
}
QPushButton#install_btn:pressed {
    background-color: #176b3a;
}
QCheckBox {
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #444444;
    background-color: #222222;
}
QCheckBox::indicator:checked {
    background-color: #00ffcc;
    border: 1px solid #00ffcc;
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
    background-color: #00ffcc;
    border-radius: 4px;
}
'''


def resource_path(relative_path):
    '''Get path to resource in PyInstaller mode or source mode.'''
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_desktop_path():
    '''Get the true active Windows Desktop folder path via Registry.'''
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
    return fallback if os.path.exists(fallback) else os.path.expanduser("~")


def get_start_menu_path():
    '''Get the Start Menu Programs folder path via Registry.'''
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


def create_shortcut_windows(target_exe, shortcut_path, icon_path=None):
    '''Create a Windows .lnk shortcut via PowerShell COM object.'''
    try:
        target_exe_clean = os.path.normpath(target_exe)
        shortcut_path_clean = os.path.normpath(shortcut_path)
        work_dir = os.path.dirname(target_exe_clean)

        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path_clean}')
$Shortcut.TargetPath = '{target_exe_clean}'
$Shortcut.WorkingDirectory = '{work_dir}'
'''
        if icon_path and os.path.exists(icon_path):
            icon_clean = os.path.normpath(icon_path)
            ps_script += f"$Shortcut.IconLocation = '{icon_clean}'\n"

        ps_script += "$Shortcut.Save()\n"

        subprocess.run(
            ["powershell", "-Command", ps_script],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
        return False


class InstallWorkerSignals(QObject):
    progress = Signal(int, str)
    finished = Signal(bool, str)


class InstallWorker(QThread):
    def __init__(self, target_dir, create_desktop, create_start_menu):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop = create_desktop
        self.create_start_menu = create_start_menu
        self.signals = InstallWorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit(5, "Preparing installation folder...")
            os.makedirs(self.target_dir, exist_ok=True)

            source_folder = resource_path("Ultimate_Quest_Folder")
            if not os.path.exists(source_folder):
                source_folder = os.path.abspath("Ultimate_Quest_Folder")

            if not os.path.exists(source_folder):
                self.signals.finished.emit(False, "Bundled Ultimate_Quest_Folder not found!")
                return

            all_files = []
            for root, dirs, files in os.walk(source_folder):
                for f in files:
                    all_files.append(os.path.join(root, f))

            total_files = len(all_files)
            if total_files == 0:
                self.signals.finished.emit(False, "No files found to install.")
                return

            self.signals.progress.emit(10, f"Copying {total_files} files...")

            copied_count = 0
            for src_file in all_files:
                rel_path = os.path.relpath(src_file, source_folder)
                dst_file = os.path.join(self.target_dir, rel_path)

                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)

                copied_count += 1
                percent = int(10 + (copied_count / total_files) * 75)
                self.signals.progress.emit(percent, f"Extracting: {rel_path}")
                time.sleep(0.01)

            main_exe = os.path.join(self.target_dir, "Ultimate_Quest.exe")
            ico_src = resource_path("icons/UQ.ico")
            ico_dst = os.path.join(self.target_dir, "app_icon.ico")

            if os.path.exists(ico_src):
                shutil.copy2(ico_src, ico_dst)
            else:
                ico_dst = main_exe

            self.signals.progress.emit(90, "Creating Windows shortcuts...")

            if self.create_desktop:
                desktop_dir = get_desktop_path()
                shortcut_path = os.path.join(desktop_dir, "Ultimate Quest.lnk")
                create_shortcut_windows(main_exe, shortcut_path, ico_dst)

            if self.create_start_menu:
                start_menu_dir = get_start_menu_path()
                if start_menu_dir:
                    os.makedirs(start_menu_dir, exist_ok=True)
                    shortcut_path = os.path.join(start_menu_dir, "Ultimate Quest.lnk")
                    create_shortcut_windows(main_exe, shortcut_path, ico_dst)

            self.signals.progress.emit(100, "Installation Complete!")
            self.signals.finished.emit(True, "Installation completed successfully!")
        except Exception as e:
            self.signals.finished.emit(False, f"Installation error: {str(e)}")


class SetupInstallerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Quest Setup")
        self.resize(650, 470)
        self.setMinimumSize(600, 440)

        app_icon = resource_path("icons/UQ.ico")
        if os.path.exists(app_icon):
            self.setWindowIcon(QIcon(app_icon))

        self.installed_dir = ""
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)

        self.stacked = QStackedWidget()

        # ── Page 0: Directory Selection & Options ──
        page0 = QWidget()
        p0_layout = QVBoxLayout(page0)
        p0_layout.setContentsMargins(0, 0, 0, 0)
        p0_layout.setSpacing(15)

        title = QLabel("Ultimate Quest Setup Wizard")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ffcc;")
        p0_layout.addWidget(title)

        subtitle = QLabel("Select installation folder and shortcut preferences:")
        subtitle.setStyleSheet("font-size: 13px; color: #cccccc;")
        p0_layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        lbl_dir = QLabel("Destination Folder:")
        lbl_dir.setStyleSheet("font-weight: bold; color: #ffffff;")
        card_layout.addWidget(lbl_dir)

        dir_row = QHBoxLayout()
        default_base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        default_dir = os.path.join(default_base, "UEQuest by E")

        self.dir_entry = QLineEdit(default_dir)
        dir_row.addWidget(self.dir_entry)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)
        dir_row.addWidget(self.browse_btn)

        card_layout.addLayout(dir_row)

        sub_note = QLabel("Files will be installed inside the 'UEQuest by E' folder.")
        sub_note.setStyleSheet("font-size: 11px; color: #888888;")
        card_layout.addWidget(sub_note)

        card_layout.addSpacing(10)

        self.chk_desktop = QCheckBox("Create Desktop Shortcut ('Ultimate Quest' on homescreen)")
        self.chk_desktop.setChecked(True)
        card_layout.addWidget(self.chk_desktop)

        self.chk_start_menu = QCheckBox("Create Start Menu Shortcut")
        self.chk_start_menu.setChecked(True)
        card_layout.addWidget(self.chk_start_menu)

        p0_layout.addWidget(card)
        p0_layout.addStretch()

        p0_btn_row = QHBoxLayout()
        p0_btn_row.addStretch()
        self.install_btn = QPushButton("Install Now")
        self.install_btn.setObjectName("install_btn")
        self.install_btn.setMinimumWidth(140)
        self.install_btn.setFixedHeight(40)
        self.install_btn.clicked.connect(self.start_installation)
        p0_btn_row.addWidget(self.install_btn)
        p0_layout.addLayout(p0_btn_row)

        self.stacked.addWidget(page0)

        # ── Page 1: Installation Progress ──
        page1 = QWidget()
        p1_layout = QVBoxLayout(page1)
        p1_layout.setContentsMargins(0, 0, 0, 0)
        p1_layout.setSpacing(20)

        p1_title = QLabel("Installing Ultimate Quest...")
        p1_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ffcc;")
        p1_layout.addWidget(p1_title)

        p1_card = QFrame()
        p1_card.setObjectName("card")
        p1_card_layout = QVBoxLayout(p1_card)
        p1_card_layout.setContentsMargins(25, 30, 25, 30)
        p1_card_layout.setSpacing(15)

        self.lbl_status = QLabel("Extracting files...")
        self.lbl_status.setStyleSheet("font-size: 13px; color: #ffffff;")
        p1_card_layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(26)
        self.progress_bar.setValue(0)
        p1_card_layout.addWidget(self.progress_bar)

        p1_layout.addWidget(p1_card)
        p1_layout.addStretch()

        self.stacked.addWidget(page1)

        # ── Page 2: Completion Page ──
        page2 = QWidget()
        p2_layout = QVBoxLayout(page2)
        p2_layout.setContentsMargins(0, 0, 0, 0)
        p2_layout.setSpacing(20)

        p2_title = QLabel("🟢 Installation Complete!")
        p2_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffcc;")
        p2_layout.addWidget(p2_title)

        p2_card = QFrame()
        p2_card.setObjectName("card")
        p2_card_layout = QVBoxLayout(p2_card)
        p2_card_layout.setContentsMargins(25, 25, 25, 25)
        p2_card_layout.setSpacing(15)

        self.lbl_installed_path = QLabel("Ultimate Quest has been installed to:")
        self.lbl_installed_path.setWordWrap(True)
        self.lbl_installed_path.setStyleSheet("font-size: 13px; color: #cccccc;")
        p2_card_layout.addWidget(self.lbl_installed_path)

        self.chk_launch = QCheckBox("Launch Ultimate Quest now")
        self.chk_launch.setChecked(True)
        p2_card_layout.addWidget(self.chk_launch)

        p2_layout.addWidget(p2_card)
        p2_layout.addStretch()

        p2_btn_row = QHBoxLayout()
        p2_btn_row.addStretch()
        self.finish_btn = QPushButton("Finish")
        self.finish_btn.setObjectName("install_btn")
        self.finish_btn.setMinimumWidth(140)
        self.finish_btn.setFixedHeight(40)
        self.finish_btn.clicked.connect(self.finish_action)
        p2_btn_row.addWidget(self.finish_btn)
        p2_layout.addLayout(p2_btn_row)

        self.stacked.addWidget(page2)

        layout.addWidget(self.stacked)
        self.setCentralWidget(central)

    def browse_folder(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Installation Directory")
        if chosen:
            chosen_path = Path(chosen)
            if chosen_path.name.lower() != "uequest by e":
                chosen_path = chosen_path / "UEQuest by E"
            self.dir_entry.setText(str(chosen_path))

    def start_installation(self):
        raw_dir = self.dir_entry.text().strip()
        if not raw_dir:
            QMessageBox.warning(self, "Invalid Path", "Please select a valid installation folder.")
            return

        target_path = Path(raw_dir)
        if target_path.name.lower() != "uequest by e":
            target_path = target_path / "UEQuest by E"

        self.installed_dir = str(target_path)
        self.stacked.setCurrentIndex(1)

        self.worker = InstallWorker(
            self.installed_dir,
            self.chk_desktop.isChecked(),
            self.chk_start_menu.isChecked()
        )
        self.worker.signals.progress.connect(self.on_progress)
        self.worker.signals.finished.connect(self.on_finished)
        self.worker.start()

    @Slot(int, str)
    def on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(message)

    @Slot(bool, str)
    def on_finished(self, success, message):
        if success:
            self.lbl_installed_path.setText(
                f"Ultimate Quest has been successfully installed to:\n\n{self.installed_dir}"
            )
            self.stacked.setCurrentIndex(2)
        else:
            QMessageBox.critical(self, "Installation Failed", message)
            self.stacked.setCurrentIndex(0)

    def finish_action(self):
        if self.chk_launch.isChecked():
            main_exe = os.path.join(self.installed_dir, "Ultimate_Quest.exe")
            if os.path.exists(main_exe):
                try:
                    subprocess.Popen([main_exe])
                except Exception as e:
                    print(f"Failed to launch: {e}")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    win = SetupInstallerApp()
    win.show()
    sys.exit(app.exec())
