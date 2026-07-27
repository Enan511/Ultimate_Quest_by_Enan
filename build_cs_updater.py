"""
build_cs_updater.py - Compiles a native C# WinForms Updater into UQ_Update_Light.exe (~2.5 MB).

Creates a standalone executable well under the 10 MB limit.
"""

import sys
import os
import zipfile
import subprocess
import shutil

MAIN_ICON_SRC = r"D:\ML practice\Icons\UQ.ico"

CS_CODE = r"""
using System;
using System.IO;
using System.IO.Compression;
using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;
using Microsoft.Win32;

namespace UltimateQuestUpdater
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    public class MainForm : Form
    {
        private TextBox txtPath;
        private Button btnBrowse;
        private Button btnUpdate;
        private Label lblStatus;
        private Label lblTitle;
        private Label lblSub;

        public MainForm()
        {
            this.Text = "Ultimate Quest Updater";
            this.Size = new System.Drawing.Size(500, 310);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(18, 18, 18);

            lblTitle = new Label();
            lblTitle.Text = "Ultimate Quest Updater";
            lblTitle.Font = new Font("Segoe UI", 16, FontStyle.Bold);
            lblTitle.ForeColor = Color.FromArgb(0, 255, 204);
            lblTitle.Location = new Point(20, 18);
            lblTitle.AutoSize = true;
            this.Controls.Add(lblTitle);

            lblSub = new Label();
            lblSub.Text = "Update existing installation to the latest version (<10 MB patch).";
            lblSub.Font = new Font("Segoe UI", 9);
            lblSub.ForeColor = Color.FromArgb(170, 170, 170);
            lblSub.Location = new Point(22, 52);
            lblSub.AutoSize = true;
            this.Controls.Add(lblSub);

            GroupBox card = new GroupBox();
            card.Location = new Point(20, 80);
            card.Size = new System.Drawing.Size(445, 90);
            card.Text = "Target Installation Directory";
            card.ForeColor = Color.White;
            card.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            card.BackColor = Color.FromArgb(30, 30, 30);
            this.Controls.Add(card);

            txtPath = new TextBox();
            txtPath.Location = new Point(15, 35);
            txtPath.Size = new System.Drawing.Size(315, 23);
            txtPath.Font = new Font("Segoe UI", 9);
            txtPath.BackColor = Color.FromArgb(45, 45, 45);
            txtPath.ForeColor = Color.White;
            txtPath.Text = AutoDetectPath();
            card.Controls.Add(txtPath);

            btnBrowse = new Button();
            btnBrowse.Text = "Browse...";
            btnBrowse.Location = new Point(340, 34);
            btnBrowse.Size = new System.Drawing.Size(85, 26);
            btnBrowse.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            btnBrowse.FlatStyle = FlatStyle.Flat;
            btnBrowse.FlatAppearance.BorderSize = 0;
            btnBrowse.BackColor = Color.FromArgb(60, 60, 60);
            btnBrowse.ForeColor = Color.White;
            btnBrowse.Click += (s, e) => {
                FolderBrowserDialog fbd = new FolderBrowserDialog();
                fbd.SelectedPath = txtPath.Text;
                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    txtPath.Text = fbd.SelectedPath;
                }
            };
            card.Controls.Add(btnBrowse);

            lblStatus = new Label();
            lblStatus.Text = "Ready to update.";
            lblStatus.Font = new Font("Segoe UI", 9);
            lblStatus.ForeColor = Color.FromArgb(200, 200, 200);
            lblStatus.Location = new Point(20, 182);
            lblStatus.Size = new System.Drawing.Size(445, 20);
            lblStatus.TextAlign = ContentAlignment.MiddleCenter;
            this.Controls.Add(lblStatus);

            btnUpdate = new Button();
            btnUpdate.Text = "Update Now";
            btnUpdate.Location = new Point(175, 210);
            btnUpdate.Size = new System.Drawing.Size(135, 38);
            btnUpdate.Font = new Font("Segoe UI", 11, FontStyle.Bold);
            btnUpdate.FlatStyle = FlatStyle.Flat;
            btnUpdate.FlatAppearance.BorderSize = 0;
            btnUpdate.BackColor = Color.FromArgb(31, 139, 76);
            btnUpdate.ForeColor = Color.White;
            btnUpdate.Click += BtnUpdate_Click;
            this.Controls.Add(btnUpdate);
        }

        private string AutoDetectPath()
        {
            try {
                Process[] procs = Process.GetProcessesByName("Ultimate_Quest");
                if (procs.Length > 0 && !string.IsNullOrEmpty(procs[0].MainModule.FileName)) {
                    string dir = Path.GetDirectoryName(procs[0].MainModule.FileName);
                    if (File.Exists(Path.Combine(dir, "Ultimate_Quest.exe"))) return dir;
                }
            } catch {}

            try {
                using (RegistryKey key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\UEQuest by E")) {
                    if (key != null) {
                        string val = key.GetValue("InstallLocation") as string;
                        if (!string.IsNullOrEmpty(val) && File.Exists(Path.Combine(val, "Ultimate_Quest.exe"))) return val;
                    }
                }
            } catch {}

            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);

            string[] candidates = new string[] {
                Path.Combine(localAppData, "UEQuest by E"),
                @"C:\Program Files\UEQuest by E",
                Path.Combine(userProfile, "Desktop", "Ultimate_Quest_Folder")
            };

            foreach (string c in candidates) {
                if (File.Exists(Path.Combine(c, "Ultimate_Quest.exe"))) return c;
            }

            return Path.Combine(localAppData, "UEQuest by E");
        }

        private void BtnUpdate_Click(object sender, EventArgs e)
        {
            string targetDir = txtPath.Text.Trim();
            if (string.IsNullOrEmpty(targetDir) || !Directory.Exists(targetDir)) {
                MessageBox.Show("Target directory does not exist:\n" + targetDir, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            btnUpdate.Enabled = false;
            lblStatus.Text = "Closing active instances...";

            System.Threading.ThreadPool.QueueUserWorkItem((state) => {
                try {
                    foreach (var p in Process.GetProcessesByName("Ultimate_Quest")) {
                        try { p.Kill(); p.WaitForExit(2000); } catch {}
                    }
                    foreach (var p in Process.GetProcessesByName("timer")) {
                        try { p.Kill(); p.WaitForExit(2000); } catch {}
                    }
                } catch {}

                this.Invoke((Action)(() => lblStatus.Text = "Extracting update payload..."));

                try {
                    var assembly = System.Reflection.Assembly.GetExecutingAssembly();
                    using (Stream stream = assembly.GetManifestResourceStream("payload.zip"))
                    {
                        if (stream != null) {
                            using (ZipArchive archive = new ZipArchive(stream)) {
                                foreach (ZipArchiveEntry entry in archive.Entries) {
                                    string destPath = Path.Combine(targetDir, entry.FullName);
                                    if (string.IsNullOrEmpty(entry.Name)) {
                                        Directory.CreateDirectory(destPath);
                                    } else {
                                        Directory.CreateDirectory(Path.GetDirectoryName(destPath));
                                        entry.ExtractToFile(destPath, true);
                                    }
                                }
                            }
                        }
                    }

                    this.Invoke((Action)(() => {
                        lblStatus.Text = "Update Completed!";
                        lblStatus.ForeColor = Color.FromArgb(0, 255, 204);
                        btnUpdate.Text = "Launch App";
                        btnUpdate.BackColor = Color.FromArgb(31, 83, 141);
                        btnUpdate.Enabled = true;
                        btnUpdate.Click -= BtnUpdate_Click;
                        btnUpdate.Click += (s, ev) => {
                            string exePath = Path.Combine(targetDir, "Ultimate_Quest.exe");
                            if (File.Exists(exePath)) Process.Start(exePath);
                            Application.Exit();
                        };

                        DialogResult dr = MessageBox.Show("Ultimate Quest has been updated successfully!\n\nWould you like to launch it now?", "Success", MessageBoxButtons.YesNo, MessageBoxIcon.Information);
                        if (dr == DialogResult.Yes) {
                            string exePath = Path.Combine(targetDir, "Ultimate_Quest.exe");
                            if (File.Exists(exePath)) Process.Start(exePath);
                            Application.Exit();
                        }
                    }));
                } catch (Exception ex) {
                    this.Invoke((Action)(() => {
                        lblStatus.Text = "Update Failed!";
                        lblStatus.ForeColor = Color.Red;
                        btnUpdate.Enabled = true;
                        MessageBox.Show("Failed to complete update:\n" + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }));
                }
            });
        }
    }
}
"""


def main():
    print("Building Native C# Lightweight Updater (UQ_Update_Light.exe)...")

    if not os.path.exists("Ultimate_Quest_Folder"):
        print("ERROR: Ultimate_Quest_Folder not found. Run UltimateQuestbyENAN.py first!")
        sys.exit(1)

    target_exe = os.path.join("Ultimate_Quest_Folder", "Ultimate_Quest.exe")
    if not os.path.exists(target_exe):
        print(f"ERROR: {target_exe} not found!")
        sys.exit(1)

    # 1. Create compressed Zip payload containing updated Ultimate_Quest.exe
    print("Step 1: Creating zip payload (payload.zip)...")
    payload_zip = "payload.zip"
    if os.path.exists(payload_zip):
        os.remove(payload_zip)

    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(target_exe, arcname="Ultimate_Quest.exe")
        timer_exe = os.path.join("Ultimate_Quest_Folder", "_internal", "timer.exe")
        if os.path.exists(timer_exe):
            zf.write(timer_exe, arcname=os.path.join("_internal", "timer.exe"))

    zip_size_mb = os.path.getsize(payload_zip) / (1024 * 1024)
    print(f"  Zip update payload size: {zip_size_mb:.2f} MB")

    # 2. Write C# source code to temporary file
    cs_file = "Updater.cs"
    with open(cs_file, "w", encoding="utf-8") as f:
        f.write(CS_CODE)

    # 3. Locate csc.exe
    csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    if not os.path.exists(csc_path):
        csc_path = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"

    if not os.path.exists(csc_path):
        print(f"ERROR: csc.exe not found at {csc_path}")
        sys.exit(1)

    # Prepare icon argument
    icon_arg = []
    if os.path.exists(MAIN_ICON_SRC):
        icon_arg = [f"/win32icon:{MAIN_ICON_SRC}"]

    out_exe = "UQ_Update_Light.exe"
    if os.path.exists(out_exe):
        os.remove(out_exe)

    cmd = [
        csc_path,
        "/target:winexe",
        "/nologo",
        f"/out:{out_exe}",
        f"/res:{payload_zip},payload.zip",
        "/r:System.IO.Compression.dll",
        "/r:System.IO.Compression.FileSystem.dll",
        "/r:System.Drawing.dll",
        "/r:System.Windows.Forms.dll",
        cs_file
    ] + icon_arg

    print("Step 2: Compiling native C# UQ_Update_Light.exe...")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print(f"ERROR compiling updater:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        sys.exit(1)

    # Cleanup temporary build files
    for file in [cs_file, payload_zip]:
        if os.path.exists(file):
            os.remove(file)

    if os.path.exists(out_exe):
        final_size_mb = os.path.getsize(out_exe) / (1024 * 1024)
        print(f"\nSUCCESS! Native Lightweight Updater Executable created: UQ_Update_Light.exe ({final_size_mb:.2f} MB)")
        if final_size_mb < 10.0:
            print(f"  VERIFIED: Executable size ({final_size_mb:.2f} MB) is well under 10 MB!")
        else:
            print(f"  WARNING: Executable size ({final_size_mb:.2f} MB) exceeds 10 MB limit!")


if __name__ == "__main__":
    main()
