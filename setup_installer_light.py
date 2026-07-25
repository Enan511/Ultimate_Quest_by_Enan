"""
setup_installer_light.py - Solid LZMA2 Compact Setup Installer for Ultimate Quest.

This script extracts a high-compression LZMA2 payload (payload.tar.xz) at runtime:
1. Target Directory Selection: Allows users to choose any installation folder.
   Enforces storing files inside a dedicated 'UEQuest by E' subfolder.
2. Shortcut Preference: Checkboxes (enabled by default) to create Desktop
   and Start Menu shortcuts pointing to Ultimate_Quest.exe.
3. Solid LZMA2 Extraction: Decompresses payload.tar.xz with a real-time progress bar.
4. Completion: Option to launch Ultimate Quest immediately upon finishing.
"""

import sys
import os
import shutil
import subprocess
import threading
import time
import tarfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None


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


class SetupInstallerLightTk:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Quest Light Setup")
        self.root.geometry("620x460")
        self.root.resizable(False, False)
        self.root.configure(bg="#121212")

        icon_path = resource_path("icons/UQ.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.installed_dir = ""

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TProgressbar", thickness=22, troughcolor="#222222", background="#00ffcc")

        self.container = tk.Frame(self.root, bg="#121212")
        self.container.pack(fill="both", expand=True, padx=25, pady=25)

        self.page_frame = None
        self.show_page_select()

    def clear_page(self):
        if self.page_frame:
            self.page_frame.destroy()
        self.page_frame = tk.Frame(self.container, bg="#121212")
        self.page_frame.pack(fill="both", expand=True)

    def show_page_select(self):
        self.clear_page()

        lbl_title = tk.Label(
            self.page_frame,
            text="Ultimate Quest Light Setup Wizard",
            font=("Segoe UI", 18, "bold"),
            fg="#00ffcc",
            bg="#121212"
        )
        lbl_title.pack(anchor="w", pady=(0, 5))

        lbl_sub = tk.Label(
            self.page_frame,
            text="Select installation folder and shortcut preferences:",
            font=("Segoe UI", 10),
            fg="#cccccc",
            bg="#121212"
        )
        lbl_sub.pack(anchor="w", pady=(0, 15))

        card = tk.Frame(self.page_frame, bg="#1a1a1a", highlightbackground="#2a2a2a", highlightthickness=1)
        card.pack(fill="x", pady=10, ipady=15, ipadx=15)

        lbl_dir = tk.Label(card, text="Destination Folder:", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#1a1a1a")
        lbl_dir.pack(anchor="w", padx=15, pady=(10, 5))

        dir_row = tk.Frame(card, bg="#1a1a1a")
        dir_row.pack(fill="x", padx=15, pady=5)

        default_base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        default_dir = os.path.join(default_base, "UEQuest by E")

        self.ent_dir = tk.Entry(
            dir_row,
            font=("Segoe UI", 10),
            bg="#222222",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            highlightbackground="#333333",
            highlightthickness=1
        )
        self.ent_dir.insert(0, default_dir)
        self.ent_dir.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 10))

        btn_browse = tk.Button(
            dir_row,
            text="Browse...",
            font=("Segoe UI", 9, "bold"),
            bg="#1f538d",
            fg="#ffffff",
            activebackground="#296cbd",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            command=self.browse_folder
        )
        btn_browse.pack(side="right")

        lbl_note = tk.Label(
            card,
            text="Files will be installed inside the 'UEQuest by E' folder.",
            font=("Segoe UI", 8),
            fg="#888888",
            bg="#1a1a1a"
        )
        lbl_note.pack(anchor="w", padx=15, pady=(2, 10))

        self.var_desktop = tk.BooleanVar(value=True)
        chk_desktop = tk.Checkbutton(
            card,
            text="Create Desktop Shortcut ('Ultimate Quest' on homescreen)",
            variable=self.var_desktop,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#1a1a1a",
            selectcolor="#222222",
            activebackground="#1a1a1a",
            activeforeground="#ffffff"
        )
        chk_desktop.pack(anchor="w", padx=15, pady=3)

        self.var_start_menu = tk.BooleanVar(value=True)
        chk_start = tk.Checkbutton(
            card,
            text="Create Start Menu Shortcut",
            variable=self.var_start_menu,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#1a1a1a",
            selectcolor="#222222",
            activebackground="#1a1a1a",
            activeforeground="#ffffff"
        )
        chk_start.pack(anchor="w", padx=15, pady=3)

        btn_row = tk.Frame(self.page_frame, bg="#121212")
        btn_row.pack(fill="x", side="bottom", pady=10)

        btn_install = tk.Button(
            btn_row,
            text="Install Now",
            font=("Segoe UI", 11, "bold"),
            bg="#1f8b4c",
            fg="#ffffff",
            activebackground="#28a85a",
            activeforeground="#ffffff",
            relief="flat",
            padx=25,
            pady=6,
            command=self.start_installation
        )
        btn_install.pack(side="right")

    def browse_folder(self):
        chosen = filedialog.askdirectory(title="Select Installation Directory")
        if chosen:
            chosen_path = Path(chosen)
            if chosen_path.name.lower() != "uequest by e":
                chosen_path = chosen_path / "UEQuest by E"
            self.ent_dir.delete(0, tk.END)
            self.ent_dir.insert(0, str(chosen_path))

    def start_installation(self):
        raw_dir = self.ent_dir.get().strip()
        if not raw_dir:
            messagebox.showwarning("Invalid Path", "Please select a valid installation folder.")
            return

        target_path = Path(raw_dir)
        if target_path.name.lower() != "uequest by e":
            target_path = target_path / "UEQuest by E"

        self.installed_dir = str(target_path)
        self.show_page_progress()

        threading.Thread(target=self.run_install_thread, daemon=True).start()

    def show_page_progress(self):
        self.clear_page()

        lbl_title = tk.Label(
            self.page_frame,
            text="Installing Ultimate Quest...",
            font=("Segoe UI", 18, "bold"),
            fg="#00ffcc",
            bg="#121212"
        )
        lbl_title.pack(anchor="w", pady=(0, 15))

        card = tk.Frame(self.page_frame, bg="#1a1a1a", highlightbackground="#2a2a2a", highlightthickness=1)
        card.pack(fill="x", pady=20, ipady=25, ipadx=20)

        self.lbl_status = tk.Label(card, text="Decompressing LZMA2 payload...", font=("Segoe UI", 10), fg="#ffffff", bg="#1a1a1a")
        self.lbl_status.pack(anchor="w", padx=15, pady=(10, 10))

        self.pbar = ttk.Progressbar(card, style="TProgressbar", maximum=100)
        self.pbar.pack(fill="x", padx=15, pady=10)

    def run_install_thread(self):
        try:
            self.update_status(5, "Preparing installation folder...")
            os.makedirs(self.installed_dir, exist_ok=True)

            payload_file = resource_path("payload.tar.xz")
            if not os.path.exists(payload_file):
                payload_file = os.path.abspath("payload.tar.xz")

            if not os.path.exists(payload_file):
                self.root.after(0, lambda: messagebox.showerror("Error", "Payload archive payload.tar.xz not found!"))
                return

            self.update_status(10, "Opening solid LZMA2 payload archive...")

            with tarfile.open(payload_file, "r:xz") as tar:
                members = tar.getmembers()
                total = len(members)
                if total == 0:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Archive is empty."))
                    return

                extracted = 0
                for member in members:
                    # Strip leading Ultimate_Quest_Folder prefix if present
                    rel_name = member.name
                    if rel_name.startswith("Ultimate_Quest_Folder/") or rel_name.startswith("Ultimate_Quest_Folder\\"):
                        rel_name = rel_name.split("/", 1)[-1].split("\\", 1)[-1]

                    if not rel_name or rel_name == "Ultimate_Quest_Folder":
                        continue

                    target_dest = os.path.join(self.installed_dir, rel_name)

                    if member.isdir():
                        os.makedirs(target_dest, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_dest), exist_ok=True)
                        with tar.extractfile(member) as s_file, open(target_dest, "wb") as d_file:
                            shutil.copyfileobj(s_file, d_file)

                    extracted += 1
                    percent = int(10 + (extracted / total) * 80)
                    self.update_status(percent, f"Extracting: {rel_name}")

            main_exe = os.path.join(self.installed_dir, "Ultimate_Quest.exe")
            ico_src = resource_path("icons/UQ.ico")
            ico_dst = os.path.join(self.installed_dir, "app_icon.ico")

            if os.path.exists(ico_src):
                shutil.copy2(ico_src, ico_dst)
            else:
                ico_dst = main_exe

            self.update_status(95, "Creating Windows shortcuts...")

            if self.var_desktop.get():
                desktop_dir = get_desktop_path()
                shortcut_path = os.path.join(desktop_dir, "Ultimate Quest.lnk")
                create_shortcut_windows(main_exe, shortcut_path, ico_dst)

            if self.var_start_menu.get():
                start_menu_dir = get_start_menu_path()
                if start_menu_dir:
                    os.makedirs(start_menu_dir, exist_ok=True)
                    shortcut_path = os.path.join(start_menu_dir, "Ultimate Quest.lnk")
                    create_shortcut_windows(main_exe, shortcut_path, ico_dst)

            self.update_status(100, "Installation Complete!")
            self.root.after(0, self.show_page_complete)
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Installation Error", err))
            self.root.after(0, self.show_page_select)

    def update_status(self, percent, message):
        self.root.after(0, lambda: self._apply_status(percent, message))

    def _apply_status(self, percent, message):
        if hasattr(self, 'pbar'):
            self.pbar['value'] = percent
        if hasattr(self, 'lbl_status'):
            self.lbl_status.config(text=message)

    def show_page_complete(self):
        self.clear_page()

        lbl_title = tk.Label(
            self.page_frame,
            text="🟢 Installation Complete!",
            font=("Segoe UI", 18, "bold"),
            fg="#00ffcc",
            bg="#121212"
        )
        lbl_title.pack(anchor="w", pady=(0, 15))

        card = tk.Frame(self.page_frame, bg="#1a1a1a", highlightbackground="#2a2a2a", highlightthickness=1)
        card.pack(fill="x", pady=15, ipady=20, ipadx=15)

        lbl_info = tk.Label(
            card,
            text=f"Ultimate Quest has been successfully installed to:\n\n{self.installed_dir}",
            font=("Segoe UI", 10),
            fg="#cccccc",
            bg="#1a1a1a",
            justify="left",
            wraplength=520
        )
        lbl_info.pack(anchor="w", padx=15, pady=(10, 15))

        self.var_launch = tk.BooleanVar(value=True)
        chk_launch = tk.Checkbutton(
            card,
            text="Launch Ultimate Quest now",
            variable=self.var_launch,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#1a1a1a",
            selectcolor="#222222",
            activebackground="#1a1a1a",
            activeforeground="#ffffff"
        )
        chk_launch.pack(anchor="w", padx=15, pady=5)

        btn_row = tk.Frame(self.page_frame, bg="#121212")
        btn_row.pack(fill="x", side="bottom", pady=10)

        btn_finish = tk.Button(
            btn_row,
            text="Finish",
            font=("Segoe UI", 11, "bold"),
            bg="#1f8b4c",
            fg="#ffffff",
            activebackground="#28a85a",
            activeforeground="#ffffff",
            relief="flat",
            padx=25,
            pady=6,
            command=self.finish_action
        )
        btn_finish.pack(side="right")

    def finish_action(self):
        if self.var_launch.get():
            main_exe = os.path.join(self.installed_dir, "Ultimate_Quest.exe")
            if os.path.exists(main_exe):
                try:
                    subprocess.Popen([main_exe])
                except Exception as e:
                    print(f"Failed to launch: {e}")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SetupInstallerLightTk(root)
    root.mainloop()
