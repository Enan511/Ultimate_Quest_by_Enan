import sys
import os
import subprocess
import shutil

from build_support import pyinstaller_environment, qt_runtime_files, runtime_binary_args, stage_app_runtime

# Build configuration mode:
# BUILD_SINGLE_FILE = False compiles the app as a folder distribution (--onedir)
# which provides instant application startup and clean file structure.
BUILD_SINGLE_FILE = False

RCEDIT_PATH = "rcedit.exe"

# Optional Steam and timer artwork can be supplied on the build machine.
MAIN_ICON_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "UQ.ico")
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
        subprocess.run(cmd, check=True, env=pyinstaller_environment())
    except FileNotFoundError:
        print(f"\nERROR during {step_name}: PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR during {step_name}: PyInstaller exited with code {e.returncode}.")
        sys.exit(1)


def main():
    """Build the timer and Ultimate Quest executables."""
    runtime_files = qt_runtime_files()
    runtime_args = runtime_binary_args(runtime_files)
    print("Step 1: Generating the Dark-Mode Timer CS Code...")
    with open("timer_app.cs", "w", encoding="utf-8") as f:
        f.write(TIMER_CS_CODE)

    print("Step 2: Compiling Lightweight Native Timer App (csc.exe)...")
    csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    if not os.path.exists(csc_path):
        csc_path = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"

    subprocess.run(
        [csc_path, "/target:winexe", "/nologo", "/r:System.Drawing.dll", "/r:System.Windows.Forms.dll",
         f"/win32icon:{MAIN_ICON_SRC}", "/out:timer.exe", "timer_app.cs"],
        check=True
    )

    print("Step 4: Preparing Icon Bundle...")
    os.makedirs("icons", exist_ok=True)
    for icon_src in TIMER_ICONS:
        if os.path.exists(icon_src):
            shutil.copy(icon_src, os.path.join("icons", os.path.basename(icon_src)))
    if os.path.exists(STEAM_ICON_SRC):
        shutil.copy(STEAM_ICON_SRC, os.path.join("icons", "Steam.ico"))
    shutil.copy(MAIN_ICON_SRC, os.path.join("icons", "UQ.ico"))
    main_icon_arg = ["--icon", MAIN_ICON_SRC]

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
    ] + runtime_args + exclusions + ["main_builder.py"]

    run_pyinstaller(cmd, "Ultimate Quest compilation")

    print("Step 7: Moving and patching output executables...")

    if BUILD_SINGLE_FILE:
        shutil.copy(os.path.join("dist", "Ultimate_Quest.exe"), "Ultimate_Quest.exe")
    else:
        out_dir = "Ultimate_Quest_Folder"
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        shutil.move(os.path.join("dist", "Ultimate_Quest"), out_dir)
        stage_app_runtime(runtime_files, out_dir)

        if os.path.exists("uninstaller.py"):
            print("Step 6b: Compiling UEQ Uninstaller.exe...")
            run_pyinstaller(
                [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
                "--name", "UEQ Uninstaller", "--add-data", f"{MAIN_ICON_SRC}{os.pathsep}icons"]
                + main_icon_arg + runtime_args + exclusions + ["uninstaller.py"],
                "Uninstaller compilation"
            )
            uninst_dist = os.path.join("dist", "UEQ Uninstaller.exe")
            if os.path.exists(uninst_dist):
                shutil.copy(uninst_dist, os.path.join(out_dir, "UEQ Uninstaller.exe"))
                print("  Bundled UEQ Uninstaller.exe into Ultimate_Quest_Folder.")

        print(f"\nSUCCESS! Your app is inside the '{out_dir}' folder.")


    for file in ["timer_app.cs", "main_builder.py", "timer.exe", "timer.spec", "Ultimate_Quest.spec"]:
        if os.path.exists(file):
            os.remove(file)
    for folder in ["build", "dist", "__pycache__", "icons"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    if BUILD_SINGLE_FILE:
        print("\nSUCCESS! You can now use 'Ultimate_Quest.exe'.")


TIMER_CS_CODE = r"""
using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;

namespace TimerApplication
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new TimerApp());
        }
    }

    public class TimerApp : Form
    {
        private Label lblTitle;
        private Label lblTimer;
        private CheckBox chkAsk;
        private Timer timer;
        private int totalSeconds;
        private string exePath;
        private string exeName;
        private string runningTimersFile;

        public TimerApp()
        {
            exePath = Process.GetCurrentProcess().MainModule.FileName;
            exeName = Path.GetFileNameWithoutExtension(exePath);

            string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string saveFolder = Path.Combine(appData, "UltimateQuest");
            Directory.CreateDirectory(saveFolder);
            runningTimersFile = Path.Combine(saveFolder, "running_timers.json");

            string candidateIcon = Path.Combine(Path.GetDirectoryName(exePath), exeName + "_icon.ico");
            try
            {
                this.Icon = File.Exists(candidateIcon) ? new Icon(candidateIcon) : Icon.ExtractAssociatedIcon(exePath);
            }
            catch {}

            this.Text = exeName;
            this.Size = new Size(350, 160);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(18, 18, 18);

            lblTitle = new Label();
            lblTitle.Text = exeName;
            lblTitle.Font = new Font("Segoe UI", 15, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.Location = new Point(10, 10);
            lblTitle.Size = new Size(315, 30);
            lblTitle.TextAlign = ContentAlignment.MiddleCenter;
            this.Controls.Add(lblTitle);

            lblTimer = new Label();
            lblTimer.Text = "00:00";
            lblTimer.Font = new Font("Segoe UI", 26, FontStyle.Bold);
            lblTimer.ForeColor = Color.FromArgb(0, 255, 204);
            lblTimer.Location = new Point(10, 40);
            lblTimer.Size = new Size(315, 45);
            lblTimer.TextAlign = ContentAlignment.MiddleCenter;
            this.Controls.Add(lblTimer);

            chkAsk = new CheckBox();
            chkAsk.Text = "Ask every time before closing";
            chkAsk.Font = new Font("Segoe UI", 9);
            chkAsk.ForeColor = Color.FromArgb(170, 170, 170);
            chkAsk.BackColor = Color.FromArgb(18, 18, 18);
            chkAsk.Checked = LoadAskSetting();
            chkAsk.Location = new Point(80, 88);
            chkAsk.AutoSize = true;
            chkAsk.CheckedChanged += (s, e) => SaveAskSetting(chkAsk.Checked);
            this.Controls.Add(chkAsk);

            Random rnd = new Random();
            totalSeconds = rnd.Next(15 * 60 + 30, 16 * 60 + 1);

            UpdateTimerDisplay();
            WriteStatus(totalSeconds);

            timer = new Timer();
            timer.Interval = 1000;
            timer.Tick += Timer_Tick;
            timer.Start();

            this.FormClosing += TimerApp_FormClosing;
        }

        private void Timer_Tick(object sender, EventArgs e)
        {
            totalSeconds--;
            if (totalSeconds <= 0)
            {
                timer.Stop();
                ScheduleSelfDelete();
                ClearStatus();
                this.FormClosing -= TimerApp_FormClosing;
                Application.Exit();
                return;
            }
            UpdateTimerDisplay();
            WriteStatus(totalSeconds);
        }

        private void UpdateTimerDisplay()
        {
            int mins = totalSeconds / 60;
            int secs = totalSeconds % 60;
            lblTimer.Text = string.Format("{0:D2}:{1:D2}", mins, secs);
        }

        private bool LoadAskSetting()
        {
            try {
                string settingsFile = Path.Combine(Path.GetDirectoryName(runningTimersFile), "settings.json");
                if (File.Exists(settingsFile)) {
                    string txt = File.ReadAllText(settingsFile);
                    if (txt.Contains("\"ask_on_manual_close\": false")) return false;
                }
            } catch {}
            return true;
        }

        private void SaveAskSetting(bool val)
        {
            try {
                string settingsFile = Path.Combine(Path.GetDirectoryName(runningTimersFile), "settings.json");
                string txt = string.Format("{{\"ask_on_manual_close\": {0}}}", val.ToString().ToLower());
                File.WriteAllText(settingsFile, txt);
            } catch {}
        }

        private void TimerApp_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (e.CloseReason == CloseReason.UserClosing)
            {
                bool askEverytime = chkAsk.Checked;
                if (!askEverytime)
                {
                    ScheduleSelfDelete();
                    ClearStatus();
                    return;
                }

                e.Cancel = true;

                using (Form dlg = new Form())
                {
                    dlg.Text = "Confirm Exit";
                    dlg.Size = new Size(420, 220);
                    dlg.FormBorderStyle = FormBorderStyle.FixedDialog;
                    dlg.MaximizeBox = false;
                    dlg.StartPosition = FormStartPosition.CenterParent;
                    dlg.BackColor = Color.FromArgb(26, 26, 26);

                    Label lbl = new Label();
                    lbl.Text = "Do you want to delete game files and manifest upon closing?";
                    lbl.Font = new Font("Segoe UI", 11);
                    lbl.ForeColor = Color.White;
                    lbl.Location = new Point(20, 20);
                    lbl.Size = new Size(360, 45);
                    lbl.TextAlign = ContentAlignment.TopCenter;
                    dlg.Controls.Add(lbl);

                    CheckBox chkDlg = new CheckBox();
                    chkDlg.Text = "Ask every time before closing";
                    chkDlg.Font = new Font("Segoe UI", 10);
                    chkDlg.ForeColor = Color.FromArgb(204, 204, 204);
                    chkDlg.Checked = chkAsk.Checked;
                    chkDlg.Location = new Point(110, 75);
                    chkDlg.AutoSize = true;
                    dlg.Controls.Add(chkDlg);

                    Button btnYes = new Button();
                    btnYes.Text = "Yes";
                    btnYes.Font = new Font("Segoe UI", 10, FontStyle.Bold);
                    btnYes.ForeColor = Color.White;
                    btnYes.BackColor = Color.FromArgb(31, 139, 76);
                    btnYes.FlatStyle = FlatStyle.Flat;
                    btnYes.FlatAppearance.BorderSize = 0;
                    btnYes.Size = new Size(110, 35);
                    btnYes.Location = new Point(70, 120);

                    Button btnNo = new Button();
                    btnNo.Text = "No";
                    btnNo.Font = new Font("Segoe UI", 10, FontStyle.Bold);
                    btnNo.ForeColor = Color.White;
                    btnNo.BackColor = Color.FromArgb(217, 56, 56);
                    btnNo.FlatStyle = FlatStyle.Flat;
                    btnNo.FlatAppearance.BorderSize = 0;
                    btnNo.Size = new Size(110, 35);
                    btnNo.Location = new Point(220, 120);

                    btnYes.Click += (s, ev) => {
                        chkAsk.Checked = chkDlg.Checked;
                        SaveAskSetting(chkDlg.Checked);
                        dlg.DialogResult = DialogResult.Yes;
                    };

                    btnNo.Click += (s, ev) => {
                        chkAsk.Checked = chkDlg.Checked;
                        SaveAskSetting(chkDlg.Checked);
                        dlg.DialogResult = DialogResult.No;
                    };

                    dlg.Controls.Add(btnYes);
                    dlg.Controls.Add(btnNo);

                    DialogResult res = dlg.ShowDialog(this);
                    if (res == DialogResult.Yes)
                    {
                        ScheduleSelfDelete();
                        ClearStatus();
                        this.FormClosing -= TimerApp_FormClosing;
                        Application.Exit();
                    }
                    else if (res == DialogResult.No)
                    {
                        ClearStatus();
                        this.FormClosing -= TimerApp_FormClosing;
                        Application.Exit();
                    }
                }
            }
        }

        private void WriteStatus(int remainingSeconds)
        {
            try {
                string content = string.Format("{{\"{0}\": {{\"remaining_seconds\": {1}, \"updated\": {2}}}}}",
                    exePath.Replace("\\", "\\\\"), remainingSeconds, DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1)).TotalSeconds);
                File.WriteAllText(runningTimersFile, content);
            } catch {}
        }

        private void ClearStatus()
        {
            try {
                if (File.Exists(runningTimersFile)) File.Delete(runningTimersFile);
            } catch {}
        }

        private void ScheduleSelfDelete()
        {
            try {
                string folder = Path.GetDirectoryName(exePath);
                string candidateIcon = Path.Combine(folder, exeName + "_icon.ico");
                string candidateManifest = Path.Combine(folder, exeName + "_manifest.path");
                string manifestTarget = string.Empty;

                if (File.Exists(candidateManifest))
                {
                    try { manifestTarget = File.ReadAllText(candidateManifest).Trim(); } catch {}
                }

                string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                string appInstallDir = Path.Combine(appData, "UEQuest by E");
                string desktopDir = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                string downloadsDir = Path.Combine(userProfile, "Downloads");
                string docsDir = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
                string progFilesX86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
                string winDir = Environment.GetFolderPath(Environment.SpecialFolder.Windows);

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = "cmd.exe";
                // The hidden cleanup process has no interactive input for timeout.exe.
                string args = string.Format("/d /c ping.exe -n 3 127.0.0.1 >nul & del /f /q \"{0}\"", exePath);
                if (File.Exists(candidateIcon)) args += string.Format(" & del /f /q \"{0}\"", candidateIcon);
                if (File.Exists(candidateManifest)) args += string.Format(" & del /f /q \"{0}\"", candidateManifest);
                if (!string.IsNullOrEmpty(manifestTarget) && File.Exists(manifestTarget)) {
                    args += string.Format(" & del /f /q \"{0}\"", manifestTarget);
                }

                bool isProtected = string.IsNullOrEmpty(folder) ||
                                   Path.GetPathRoot(folder).Equals(folder, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(appInstallDir, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(desktopDir, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(downloadsDir, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(docsDir, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(progFiles, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(progFilesX86, StringComparison.OrdinalIgnoreCase) ||
                                   folder.Equals(winDir, StringComparison.OrdinalIgnoreCase);

                if (!isProtected)
                {
                    args += string.Format(" & rmdir \"{0}\"", folder);
                    string parentFolder = Path.GetDirectoryName(folder);
                    if (!string.IsNullOrEmpty(parentFolder))
                    {
                        bool isParentProtected = Path.GetPathRoot(parentFolder).Equals(parentFolder, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(appInstallDir, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(desktopDir, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(downloadsDir, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(docsDir, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(progFiles, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(progFilesX86, StringComparison.OrdinalIgnoreCase) ||
                                                 parentFolder.Equals(winDir, StringComparison.OrdinalIgnoreCase);
                        if (!isParentProtected)
                        {
                            args += string.Format(" & rmdir \"{0}\"", parentFolder);
                        }
                    }
                }

                psi.Arguments = args;
                psi.WindowStyle = ProcessWindowStyle.Hidden;
                psi.CreateNoWindow = true;
                using (Process cleanup = Process.Start(psi))
                {
                    if (cleanup != null)
                    {
                        string cleanupDir = Path.Combine(appData, "UltimateQuest", "cleanup");
                        Directory.CreateDirectory(cleanupDir);
                        string marker = Path.Combine(cleanupDir, Guid.NewGuid().ToString("N") + ".txt");
                        double started = cleanup.StartTime.ToUniversalTime().Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
                        File.WriteAllText(marker + ".tmp", cleanup.Id + " " + started.ToString(System.Globalization.CultureInfo.InvariantCulture));
                        File.Move(marker + ".tmp", marker);
                    }
                }
            } catch {}
        }
    }
}
"""

BUILDER_CODE = r"""
import sys
import os
import shutil
import subprocess
import threading
import psutil
import json
import ntpath
import time
import tempfile
import random
import struct
import requests
import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QLabel, QTextEdit, QLineEdit, QScrollArea,
    QMessageBox, QDialog, QInputDialog, QMenu, QFrame, QSizePolicy, QStyle,
    QStackedWidget, QComboBox, QListWidget, QSystemTrayIcon
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject, QLockFile
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
SCHEDULER_FILE = Path(SAVE_FOLDER) / "scheduler.json"
CLEANUP_FOLDER = Path(SAVE_FOLDER) / "cleanup"
# Timers generated by earlier releases do not publish cleanup process IDs.
LEGACY_CLEANUP_GRACE = 3.0

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


def is_protected_directory(dir_path):
    '''Check if directory is a protected/system directory.'''
    try:
        norm = os.path.normpath(os.path.abspath(dir_path)).lower()
        drive, tail = os.path.splitdrive(norm)
        if not tail or tail == os.sep:
            return True
        appdata = (os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")).lower()
        app_install = os.path.normpath(os.path.join(appdata, "uequest by e")).lower()
        desktop = os.path.normpath(os.path.expanduser("~/desktop")).lower()
        downloads = os.path.normpath(os.path.expanduser("~/downloads")).lower()
        documents = os.path.normpath(os.path.expanduser("~/documents")).lower()
        prog_files = os.path.normpath(os.environ.get("ProgramFiles", "C:/Program Files")).lower()
        prog_files_x86 = os.path.normpath(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")).lower()
        windir = os.path.normpath(os.environ.get("WINDIR", "C:/Windows")).lower()
        temp_dir = os.path.normpath(os.environ.get("TEMP", "C:/Windows/Temp")).lower()

        if norm in (app_install, desktop, downloads, documents, prog_files, prog_files_x86, windir, temp_dir):
            return True
        return False
    except Exception:
        return True


def safe_remove_empty_dir(dir_path):
    '''Remove directory only if completely empty and not protected. Walks upward safely.'''
    try:
        if not dir_path:
            return
        norm = os.path.normpath(os.path.abspath(dir_path))
        if is_protected_directory(norm):
            return
        if os.path.exists(norm) and os.path.isdir(norm):
            if not os.listdir(norm):
                os.rmdir(norm)
                parent = os.path.dirname(norm)
                if parent and parent != norm:
                    safe_remove_empty_dir(parent)
    except Exception:
        pass


def normalize_path_key(path):
    '''Normalize path key.'''
    return os.path.normpath(path).lower()


def game_search_rank(query, game_name, exe_path):
    '''Return the match rank, or None when neither name matches.'''
    filename = ntpath.basename(exe_path)
    fields = (game_name.casefold(), filename.casefold(), ntpath.splitext(filename)[0].casefold())
    query = query.casefold().strip()
    if query in fields:
        return 0

    compact_query = ''.join(ch for ch in query if ch.isalnum())
    compact_fields = [''.join(ch for ch in field if ch.isalnum()) for field in fields]
    if compact_query and compact_query in compact_fields:
        return 1
    if any(query in field for field in fields) or (
        compact_query and any(compact_query in field for field in compact_fields)
    ):
        return 2
    return None


def cleanup_is_running():
    '''Check cleanup workers by PID and start time, including across app restarts.'''
    pending = False
    for marker in CLEANUP_FOLDER.glob("*.txt"):
        try:
            pid, started = marker.read_text(encoding="utf-8").split()
            process = psutil.Process(int(pid))
            if abs(process.create_time() - float(started)) < 1:
                pending = True
                continue
        except psutil.AccessDenied:
            pending = True
            continue
        except (psutil.NoSuchProcess, ValueError, FileNotFoundError):
            pass
        marker.unlink(missing_ok=True)
    return pending


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
    game_launch_finished = Signal(dict, bool, object, str)


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
        self.scheduler_state = self.load_scheduler()
        self.scheduler_error = ""
        self.scheduler_launching = False
        self.launched_processes = {}
        self.running_games = {}
        self.queue_ready_at = time.monotonic() + LEGACY_CLEANUP_GRACE if self.queue else 0
        self.quit_requested = False

        self.current_mode = "standard"  # "standard" or "steam"
        self.selected_steam_game = None

        self.signals = WorkerSignals()
        self.signals.gist_check_complete.connect(self.handle_new_quests)
        self.signals.gist_check_empty.connect(self.handle_empty_quests)
        self.signals.gist_check_error.connect(self.handle_gist_error)
        self.signals.steam_search_complete.connect(self.handle_steam_results)
        self.signals.game_launch_finished.connect(self.finish_game_launch)

        self.settings = self.load_settings()
        self.setup_ui()
        self.setup_tray()
        self.load_history()
        self.refresh_queue()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_running_processes)
        self.poll_timer.start(2000)
        QTimer.singleShot(0, self.poll_running_processes)

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
        self.check_quests_btn.setToolTip("Check for new quests (Ctrl+N)")
        self.check_quests_btn.clicked.connect(self.start_gist_check_thread)
        top_bar.addWidget(self.check_quests_btn)

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

        # Launch mode and local game search
        search_row = QHBoxLayout()
        self.launch_mode = QComboBox()
        self.launch_mode.addItem("Launcher Mode", "launcher")
        self.launch_mode.addItem("Scheduler Mode", "scheduler")
        self.launch_mode.setAccessibleName("Launch mode")
        self.launch_mode.setCurrentIndex(self.launch_mode.findData(self.scheduler_state["mode"]))
        self.launch_mode.currentIndexChanged.connect(self.change_launch_mode)
        search_row.addWidget(self.launch_mode)
        search_row.addStretch()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search game or executable name")
        self.search_entry.setMaximumWidth(340)
        self.search_entry.setClearButtonEnabled(True)
        self.search_entry.setFixedHeight(35)
        self.search_entry.textChanged.connect(self.refresh_lists)
        search_row.addWidget(self.search_entry)
        central_layout.addLayout(search_row)

        lists_row = QHBoxLayout()
        game_lists = QVBoxLayout()
        lists_row.addLayout(game_lists, 3)
        central_layout.addLayout(lists_row, 1)

        # ── Created Executable History List ──
        self.lbl_built = QLabel("Created Executable History")
        self.lbl_built.setStyleSheet("font-size: 15px; font-weight: bold; color: #00ffcc;")
        game_lists.addWidget(self.lbl_built)

        self.built_scroll = QScrollArea()
        self.built_scroll_widget = QWidget()
        self.built_scroll_layout = QVBoxLayout(self.built_scroll_widget)
        self.built_scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.built_scroll_layout.setSpacing(5)
        self.built_scroll_widget.setStyleSheet("background-color: #181818;")
        self.built_scroll.setWidgetResizable(True)
        self.built_scroll.setWidget(self.built_scroll_widget)
        self.built_scroll.setMinimumHeight(self._scroll_height_for_rows(1))
        game_lists.addWidget(self.built_scroll)

        # ── Game List (Unbuilt) ──
        self.lbl_unbuilt = QLabel("Game List")
        self.lbl_unbuilt.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffcc00;")
        game_lists.addWidget(self.lbl_unbuilt)

        self.unbuilt_scroll = QScrollArea()
        self.unbuilt_scroll_widget = QWidget()
        self.unbuilt_scroll_layout = QVBoxLayout(self.unbuilt_scroll_widget)
        self.unbuilt_scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.unbuilt_scroll_layout.setSpacing(5)
        self.unbuilt_scroll_widget.setStyleSheet("background-color: #181818;")
        self.unbuilt_scroll.setWidgetResizable(True)
        self.unbuilt_scroll.setWidget(self.unbuilt_scroll_widget)
        self.unbuilt_scroll.setMinimumHeight(self._scroll_height_for_rows(1))
        game_lists.addWidget(self.unbuilt_scroll)

        game_lists.addStretch()
        self.queue_panel = QWidget()
        self.queue_panel.setMinimumWidth(215)
        queue_layout = QVBoxLayout(self.queue_panel)
        queue_layout.setContentsMargins(8, 0, 0, 0)
        queue_title = QLabel("Launch Queue")
        queue_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00ffcc;")
        queue_layout.addWidget(queue_title)
        self.queue_status = QLabel()
        self.queue_status.setTextFormat(Qt.PlainText)
        self.queue_status.setWordWrap(True)
        queue_layout.addWidget(self.queue_status)
        self.queue_list = QListWidget()
        self.queue_list.setAccessibleName("Queued games")
        self.queue_list.setMinimumHeight(60)
        self.queue_list.currentRowChanged.connect(self.update_queue_controls)
        queue_layout.addWidget(self.queue_list, 1)
        queue_controls = QHBoxLayout()
        self.queue_up_btn = QPushButton("Up")
        self.queue_up_btn.clicked.connect(lambda: self.edit_queue(-1))
        queue_controls.addWidget(self.queue_up_btn)
        self.queue_down_btn = QPushButton("Down")
        self.queue_down_btn.clicked.connect(lambda: self.edit_queue(1))
        queue_controls.addWidget(self.queue_down_btn)
        self.queue_remove_btn = QPushButton("Remove")
        self.queue_remove_btn.clicked.connect(lambda: self.edit_queue(None))
        queue_controls.addWidget(self.queue_remove_btn)
        queue_layout.addLayout(queue_controls)
        self.queue_pause_btn = QPushButton("Pause Queue")
        self.queue_pause_btn.clicked.connect(self.toggle_queue_pause)
        queue_layout.addWidget(self.queue_pause_btn)
        lists_row.addWidget(self.queue_panel, 2)

        self.setCentralWidget(central_widget)

    @property
    def queue(self):
        return self.scheduler_state["queue"]

    @property
    def scheduler_mode(self):
        return self.scheduler_state["mode"] == "scheduler"

    @staticmethod
    def load_scheduler():
        defaults = {"mode": "launcher", "paused": False, "queue": [], "failure": ""}
        try:
            state = json.loads(SCHEDULER_FILE.read_text(encoding="utf-8"))
            if state["mode"] in ("launcher", "scheduler") and isinstance(state["queue"], list):
                return {
                    "mode": state["mode"],
                    "paused": bool(state.get("paused", False)),
                    "failure": state.get("failure") or "",
                    "queue": [entry for entry in state["queue"] if isinstance(entry, dict)
                              and isinstance(entry.get("exe_path"), str) and entry["exe_path"]],
                }
        except FileNotFoundError:
            pass
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"Could not load the launch queue: {exc}")
        return defaults

    def save_scheduler(self, **changes):
        state = {**self.scheduler_state, **changes}
        temporary = SCHEDULER_FILE.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
            temporary.replace(SCHEDULER_FILE)
        except OSError as exc:
            self.scheduler_error = f"Could not save the launch queue: {exc}"
            self.statusBar().showMessage(self.scheduler_error, 10000)
            return False
        self.scheduler_state = state
        self.scheduler_error = ""
        return True

    def setup_tray(self):
        self.tray_icon = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = self.windowIcon()
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Ultimate Quest")
        tray_menu = QMenu(self)
        tray_menu.addAction("Open Ultimate Quest", self.restore_window)
        tray_menu.addAction("Quit", self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_window()

    def restore_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.quit_requested = True
        if self.close():
            QApplication.quit()

    def closeEvent(self, event):
        if self.scheduler_mode and not self.quit_requested and self.tray_icon:
            self.hide()
            event.ignore()
            return
        if self.scheduler_launching:
            self.quit_requested = True
            event.ignore()
            return
        if self.tray_icon:
            self.tray_icon.hide()
        super().closeEvent(event)

    def change_launch_mode(self):
        mode = self.launch_mode.currentData()
        if not self.save_scheduler(mode=mode):
            self.launch_mode.blockSignals(True)
            self.launch_mode.setCurrentIndex(self.launch_mode.findData(self.scheduler_state["mode"]))
            self.launch_mode.blockSignals(False)
        self.refresh_queue()
        self.refresh_lists()
        self.advance_scheduler(self.get_running_exes(max_age=0))

    def refresh_queue(self, selected=None):
        self.queue_panel.setVisible(self.scheduler_mode)
        if self.tray_icon:
            self.tray_icon.setVisible(self.scheduler_mode)
        if selected is None:
            selected = self.queue_list.currentRow()
        self.queue_list.clear()
        for position, entry in enumerate(self.queue, 1):
            filename = ntpath.basename(entry["exe_path"])
            name = entry.get("game_name") or filename
            self.queue_list.addItem(f"{position}. {name}\n{filename}")
            self.queue_list.item(position - 1).setToolTip(entry["exe_path"])
        if selected >= 0:
            self.queue_list.setCurrentRow(min(selected, len(self.queue) - 1))
        self.update_queue_controls()
        self.update_queue_status()

    def update_queue_controls(self):
        selected = self.queue_list.currentRow()
        first_editable = int(self.scheduler_launching)
        self.queue_up_btn.setEnabled(first_editable < selected < len(self.queue))
        self.queue_down_btn.setEnabled(first_editable <= selected < len(self.queue) - 1)
        self.queue_remove_btn.setEnabled(first_editable <= selected < len(self.queue))
        self.queue_pause_btn.setText("Resume Queue" if self.scheduler_state["paused"] else "Pause Queue")

    def update_queue_status(self, waiting_for_cleanup=False):
        if self.scheduler_error:
            status = self.scheduler_error
        elif self.scheduler_launching:
            entry = self.queue[0]
            status = f"Launching {entry.get('game_name') or ntpath.basename(entry['exe_path'])}…"
        elif self.scheduler_state["paused"]:
            status = self.scheduler_state["failure"] or "Queue paused"
        elif waiting_for_cleanup:
            status = "Waiting for game cleanup…"
        else:
            status = f"{len(self.queue)} queued" if self.queue else "No games queued"
        if self.running_games:
            names = ", ".join(sorted(set(self.running_games.values()), key=str.casefold))
            status = f"Running {names}\n{status}"
        self.queue_status.setText(status)

    def toggle_queue_pause(self):
        self.save_scheduler(paused=not self.scheduler_state["paused"], failure="")
        self.update_queue_controls()
        self.advance_scheduler(self.get_running_exes(max_age=0))

    def edit_queue(self, offset):
        selected = self.queue_list.currentRow()
        first_editable = int(self.scheduler_launching)
        if not first_editable <= selected < len(self.queue):
            return
        queue = self.queue.copy()
        destination = selected if offset is None else selected + offset
        if not first_editable <= destination < len(queue):
            return
        entry = queue.pop(selected)
        if offset is not None:
            queue.insert(destination, entry)
        failure = self.scheduler_state["failure"] if queue and queue[0] is self.queue[0] else ""
        self.save_scheduler(queue=queue, failure=failure)
        self.refresh_queue(destination)

    def enqueue_games(self, entries, allow_repeat=False):
        queue = self.queue.copy()
        positions = {}
        for index, entry in enumerate(queue, 1):
            positions.setdefault(normalize_path_key(resolve_path(entry["exe_path"])), index)
        duplicate_position = None
        for entry in entries:
            key = normalize_path_key(resolve_path(entry["exe_path"]))
            if key in positions and not allow_repeat:
                duplicate_position = positions[key]
                continue
            queue.append(entry)
            positions[key] = len(queue)
        if len(queue) != len(self.queue):
            self.save_scheduler(queue=queue)
        elif duplicate_position is not None:
            self.statusBar().showMessage(f"Already queued at position {duplicate_position}. Use Queue Again to repeat it.", 5500)
        self.refresh_queue()
        self.advance_scheduler(self.get_running_exes(max_age=0))

    def advance_scheduler(self, running_exes):
        with self._data_lock:
            tracked = {normalize_path_key(resolve_path(entry["exe_path"])):
                       entry.get("game_name") or ntpath.basename(entry["exe_path"])
                       for entry in self.history + self.queue}
        running = {path: tracked[path] for path in running_exes & tracked.keys()}
        for process, entry in list(self.launched_processes.items()):
            path = normalize_path_key(resolve_path(entry["exe_path"]))
            if process.poll() is None:
                running[path] = entry["game_name"]
            else:
                self.launched_processes.pop(process)
                self.queue_ready_at = time.monotonic() + LEGACY_CLEANUP_GRACE
        if self.running_games.keys() - running.keys():
            self.queue_ready_at = time.monotonic() + LEGACY_CLEANUP_GRACE
        self.running_games = running

        waiting_for_cleanup = False
        if (self.scheduler_mode and not self.scheduler_state["paused"] and self.queue
                and not self.quit_requested and not self.scheduler_launching
                and not running and not self.currently_building):
            try:
                waiting_for_cleanup = time.monotonic() < self.queue_ready_at or cleanup_is_running()
            except OSError as exc:
                self.update_queue_status()
                self.queue_status.setText(f"Could not check game cleanup: {exc}")
                return
            if not waiting_for_cleanup:
                self.scheduler_launching = True
                self.start_game_launches([self.queue[0]], allow_build=True, scheduled=True)
                self.update_queue_controls()
        self.update_queue_status(waiting_for_cleanup)

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
        '''Register the selected Steam game and launch or queue it.'''
        if not self.selected_steam_game:
            QMessageBox.warning(self, "No Game to Build", "No game to build. Please search and select a valid Steam game first.")
            return

        info = self.selected_steam_game
        game_name = info["name"]
        exe_path = info["target_rel"]
        with self._data_lock:
            key = normalize_path_key(resolve_path(exe_path))
            entry = next((item for item in self.history
                          if normalize_path_key(resolve_path(item["exe_path"])) == key), None)
            if entry is None:
                entry = {"exe_path": exe_path, "game_name": game_name, "ever_built": False}
                self.history.append(entry)
            entry["steam"] = {field: info.get(field) for field in ("appid", "installdir", "depot_id")}
        self.save_history()
        self.request_game_launches([entry["exe_path"]])

    def request_game_launches(self, paths, allow_build=True, allow_repeat=False):
        with self._data_lock:
            by_path = {normalize_path_key(resolve_path(item["exe_path"])): item.copy() for item in self.history}
        keys = dict.fromkeys(normalize_path_key(resolve_path(path)) for path in paths)
        entries = [by_path[key] for key in keys if key in by_path]
        if not entries:
            return
        if self.scheduler_mode:
            self.enqueue_games(entries, allow_repeat)
            self.refresh_lists()
        else:
            entries = [entry for entry in entries if entry["exe_path"] not in self.currently_building]
            if entries:
                self.start_game_launches(entries, allow_build)

    def start_game_launches(self, entries, allow_build, scheduled=False):
        self.currently_building.update(entry["exe_path"] for entry in entries)
        self.refresh_lists()
        threading.Thread(target=self.launch_games, args=(entries, allow_build, scheduled), daemon=True).start()

    def launch_games(self, entries, allow_build, scheduled):
        for entry in entries:
            try:
                process = self.prepare_and_launch(entry, allow_build)
            except Exception as exc:
                self.signals.game_launch_finished.emit(entry, scheduled, None, str(exc))
            else:
                self.signals.game_launch_finished.emit(entry, scheduled, process, "")

    def prepare_and_launch(self, entry, allow_build):
        target = Path(resolve_path(entry["exe_path"]))
        needs_build = not target.is_file()
        if needs_build:
            if not allow_build:
                raise FileNotFoundError(f"Executable not found: {target}")
            source = Path(resource_path("timer.exe"))
            if not source.is_file():
                raise FileNotFoundError("Bundled timer.exe not found")
            target.parent.mkdir(parents=True, exist_ok=True)

        manifest = self.prepare_steam_manifest(entry, target) if allow_build else None
        if manifest:
            target.with_name(f"{target.stem}_manifest.path").write_text(manifest, encoding="utf-8")
        if needs_build:
            build_random_icon_file(str(target.with_name(f"{target.stem}_icon.ico")))
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temp_file:
                temporary = Path(temp_file.name)
            try:
                shutil.copyfile(source, temporary)
                temporary.rename(target)
            finally:
                temporary.unlink(missing_ok=True)

        if needs_build or manifest:
            with self._data_lock:
                for item in self.history:
                    if item["exe_path"] == entry["exe_path"]:
                        item.update(root_dir=str(target.parent), ever_built=True)
                        if manifest:
                            item["manifest_path"] = manifest
                        self.save_history()
                        break
        return subprocess.Popen([str(target)])

    def prepare_steam_manifest(self, entry, target):
        steam = entry.get("steam")
        recorded = entry.get("manifest_path")
        if not steam:
            if not recorded:
                return None
            manifest = Path(recorded)
            if manifest.is_file():
                return str(manifest)
            # Older history saved the manifest path without the Steam search metadata.
            appid = manifest.stem.removeprefix("appmanifest_")
            if not appid.isdecimal():
                return None
            try:
                installdir = target.relative_to(manifest.parent / "common").parts[0]
            except (ValueError, IndexError):
                return None
            steam = {"appid": appid, "installdir": installdir}
            steam_path = manifest.parent.parent
        else:
            steam_path = get_steam_path()
            if steam_path is None:
                return None
            manifest = steam_path / "steamapps" / f"appmanifest_{steam['appid']}.acf"
            if manifest.is_file():
                reference = target.with_name(f"{target.stem}_manifest.path")
                if recorded and normalize_path_key(recorded) == normalize_path_key(str(manifest)):
                    return str(manifest)
                if reference.is_file():
                    referenced_path = reference.read_text(encoding="utf-8").strip()
                    if normalize_path_key(referenced_path) == normalize_path_key(str(manifest)):
                        return str(manifest)
                return None

        manifest_path = generate_appmanifest(steam["appid"], entry["game_name"], steam["installdir"],
                                             steam_path, steam.get("depot_id"))
        if not manifest_path:
            raise OSError(f"Could not create Steam manifest: {manifest}")
        return manifest_path

    @Slot(dict, bool, object, str)
    def finish_game_launch(self, entry, scheduled, process, error):
        self.currently_building.discard(entry["exe_path"])
        if process is not None:
            self.launched_processes[process] = entry
            self._running_exes_cache_time = 0

        if scheduled:
            self.scheduler_launching = False
            if error:
                failure = f"Queue paused. Could not launch {entry['game_name']}: {error}"
                if not self.save_scheduler(paused=True, failure=failure):
                    self.scheduler_state.update(paused=True, failure=failure)
            else:
                remaining = self.queue[1:]
                if not self.save_scheduler(queue=remaining):
                    self.scheduler_state.update(queue=remaining, paused=True)
            self.refresh_queue()
        elif error:
            QMessageBox.critical(self, "Launch Failed", f"Could not launch {entry['game_name']}: {error}")
        self.refresh_lists()
        if self.quit_requested:
            self.quit_app()
        else:
            self.advance_scheduler(self.get_running_exes())

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
                # Ensure isolated subfolder if bare filename provided
                parts = Path(e_path).parts
                if not Path(e_path).is_absolute() and len(parts) == 1:
                    e_path = str(Path("Games") / Path(e_path).stem / e_path)
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

            # Ensure isolated subfolder if bare filename provided
            parts = Path(e_path).parts
            if not Path(e_path).is_absolute() and len(parts) == 1:
                e_path = str(Path("Games") / Path(e_path).stem / e_path)

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
                elif trigger_build and (self.scheduler_mode or not os.path.exists(resolve_path(e_path))):
                    added_paths.append(e_path)

        if valid_input:
            self.save_history()
            self.refresh_lists()
            self.bulk_entry.clear()

        return added_paths

    def build_now_action(self):
        self.request_game_launches(self.add_bulk_games(trigger_build=True))

    def delete_tracked_item(self, exe_path):
        with self._data_lock:
            manifest_path = None
            for item in self.history:
                if item["exe_path"] == exe_path:
                    manifest_path = item.get("manifest_path")
                    break

        resolved_exe = resolve_path(exe_path)
        try:
            # 1. Delete Steam appmanifest if exists
            if manifest_path and os.path.exists(manifest_path):
                try:
                    os.remove(manifest_path)
                except Exception:
                    pass

            # 2. Delete game specific files
            p = Path(resolved_exe)
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

            icon_candidate = p.with_name(p.stem + "_icon.ico")
            if icon_candidate.exists():
                try:
                    icon_candidate.unlink()
                except Exception:
                    pass

            manifest_ref = p.with_name(p.stem + "_manifest.path")
            if manifest_ref.exists():
                try:
                    manifest_ref.unlink()
                except Exception:
                    pass

            # 3. Safely remove empty game directory and prune empty parents
            safe_remove_empty_dir(p.parent)

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
                    running.add(normalize_path_key(os.path.abspath(exe_path)))
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
        search_query = self.search_entry.text().strip()
        build_label = "Add to Queue" if self.scheduler_mode else "Build Now"
        self.build_now_std_btn.setText(build_label)
        self.build_now_steam_btn.setText(build_label)
        with self._data_lock:
            history_snapshot = sorted(self.history, key=lambda item: item.get("game_name", "").casefold())
        if search_query:
            matches = []
            for item in history_snapshot:
                rank = game_search_rank(search_query, item.get("game_name", ""), item["exe_path"])
                if rank is not None:
                    matches.append((rank, item))
            history_snapshot = [item for _, item in sorted(matches, key=lambda match: match[0])]

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

            filename = ntpath.basename(exe_path)
            lbl = QLabel(f"{g_name}\n{filename}")
            lbl.setTextFormat(Qt.PlainText)
            lbl.setToolTip(exe_path)
            lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
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

                btn_rerun = QPushButton("Queue" if self.scheduler_mode else "Rerun")
                btn_rerun.setFixedWidth(80)
                btn_rerun.setStyleSheet(STYLE_RERUN_BTN)
                btn_rerun.clicked.connect(lambda checked=False, p=exe_path: self.request_game_launches([p], allow_build=False))
                btn_row.addWidget(btn_rerun)

                btn_del = QPushButton("Delete Path")
                btn_del.setFixedWidth(110)
                btn_del.setStyleSheet(STYLE_DELETE_BTN)
                btn_del.clicked.connect(lambda checked=False, p=exe_path: self.delete_tracked_item(p))
                btn_row.addWidget(btn_del)

                is_running = normalize_path_key(resolved_exe) in running_exes
                if is_running:
                    btn_del.setEnabled(False)
                    btn_del.setText("Running...")
                    btn_del.setStyleSheet(STYLE_DISABLED_BTN)
                    if not self.scheduler_mode:
                        btn_rerun.setEnabled(False)
                        btn_rerun.setStyleSheet(STYLE_DISABLED_BTN)
                if exe_path in self.currently_building:
                    btn_del.setEnabled(False)
                    btn_rerun.setEnabled(False)

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
                    label = "Queue" if self.scheduler_mode else "Rebuild" if ever_built else "Build"
                    btn_build = QPushButton(label)
                    btn_build.setFixedWidth(100)
                    btn_build.setStyleSheet(STYLE_BUILD_BTN)
                    btn_build.clicked.connect(lambda checked=False, p=exe_path: self.request_game_launches([p]))
                frame_layout.addWidget(btn_build)

                self.ui_items[exe_path] = {
                    "btn_build": btn_build,
                    "is_running": False,
                    "state": "unbuilt",
                    "game_name": g_name
                }

            parent_layout.addWidget(item_frame)

        built_h, unbuilt_h = self._compute_scroll_heights(built_count, unbuilt_count)
        self.built_scroll.setMaximumHeight(built_h)
        self.unbuilt_scroll.setMaximumHeight(unbuilt_h)

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

        if self.scheduler_mode:
            act_repeat = QAction("Queue Again", menu)
            act_repeat.triggered.connect(lambda: self.request_game_launches([exe_path], allow_repeat=True))
            menu.addAction(act_repeat)

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
        if exe_path in self.currently_building or normalize_path_key(resolved_exe) in self.get_running_exes():
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
        running_timers = {normalize_path_key(path): info for path, info in read_running_timers().items()}
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

                normalized_target = normalize_path_key(resolved_exe)
                is_running = normalized_target in running_exes

                if is_running and not data["is_running"]:
                    data["btn_delete"].setEnabled(False)
                    data["btn_delete"].setText("Running...")
                    data["btn_delete"].setStyleSheet(STYLE_DISABLED_BTN)
                    if not self.scheduler_mode:
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
        self.advance_scheduler(running_exes)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icons/UQ.ico")))
    app_lock = QLockFile(str(Path(SAVE_FOLDER) / "ultimate-quest.lock"))
    app_lock.setStaleLockTime(0)
    if not app_lock.tryLock(0):
        if app_lock.error() == QLockFile.LockFailedError:
            QMessageBox.information(None, "Ultimate Quest", "Ultimate Quest is already running. Check the system tray.")
            sys.exit(0)
        QMessageBox.critical(None, "Ultimate Quest", "Could not lock the application data folder.")
        sys.exit(1)
    app.setStyleSheet(DARK_THEME)
    window = ExeBuilderApp()
    window.show()
    sys.exit(app.exec())
"""

if __name__ == "__main__":
    main()
