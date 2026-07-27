# Ultimate Quest

A modern PySide6 desktop application designed for Discord Quest game spoofing and countdown tracking. Features standard executable spoofing, **Steam Quest Mode** with real-time Steam Store search and fake `appmanifest_<appid>.acf` generation, a lightweight native C# countdown timer, embedded custom icons, standalone PySide6 & LZMA2 setup installers, and a standalone lightweight updater (<10 MB).

---

## Key Features

- **Standard Quest Spoofing** — Add games via bulk text input or sync with remote Gist quest lists.
- **Steam Quest Mode** — Integrated Steam Store search (`store.steampowered.com/api/storesearch/`) and SteamCMD API metadata extraction. Automatically generates fake `appmanifest_<appid>.acf` files (`StateFlags 1026`) in `Steam/steamapps/` for advanced quest validation (e.g., *Marathon*, *Toxic Commando Demo*).
- **Morphing Card UI** — PySide6 `QStackedWidget` interface cleanly toggles upper section between Standard Mode and Steam Mode views without UI clutter.
- **Ultra-Lightweight C# Countdown Timer** — Compiles a native 18 KB dark-mode C# timer executable (`timer.exe`) with 0 ms launch time, real-time countdown display, and preference toggles.
- **Interactive Manual Exit Protocol** — Custom exit confirmation dialog (*"Do you want to delete game files upon closing?"*) featuring **Yes** (Green: deletes files + closes game) and **No** (Red: closes game without deleting files) controls, along with an `"Ask every time before closing"` preference toggle inside the timer window.
- **Dynamic Cleanup** — Timer triggers a windowless background C# binary (`deleter.exe`) via Windows' built-in `csc.exe` to handle post-exit file, folder, icon, and manifest cleanup.
- **Standalone Lightweight Updater (`UQ_Update_Light.exe`)** — A ultra-compact updater (~4.67 MB, well under 10 MB) that auto-detects existing installed directories from running processes, shortcuts, or registry, gracefully closes active processes, and applies updates in-place.
- **Dual Setup Installers**:
  - **Full Setup (`Ultimate_Quest_Setup.exe`)** — Bundles application files along with the standalone **`UEQ Uninstaller.exe`** utility.
  - **Lightweight Setup (`UQ Setup_Light.exe`)** — Solid LZMA2 compressed installer (~46 MB) for fast downloads.

---

## Requirements

- Windows 10 / 11
- Python 3.10+

```bash
pip install -r Requirements.txt
```

---

## Building from Source

### Step 1: Build the Core Application Package

Run the main builder script:

```bash
python UltimateQuestbyENAN.py
```

This compiles `timer_app.cs` into `timer.exe` (18 KB), bundles custom icons (`UQ.ico`, `Steam.ico`, `Jett.ico`, `Ahri.ico`), compiles `uninstaller.py` into `UEQ Uninstaller.exe`, and builds the main application folder (`Ultimate_Quest_Folder`).

### Step 2: Build the Setup Installers & Lightweight Updater

To create the Full Installer (with Uninstaller):

```bash
python build_setup.py
```

To create the Compact LZMA2 Installer:

```bash
python build_setup_light.py
```

To create the Standalone Lightweight Updater (<10 MB):

```bash
python build_cs_updater.py
```

---

## Installation & Setup

1. Run `Ultimate_Quest_Setup.exe` (Full) or `UQ Setup_Light.exe` (Compact).
2. Select your preferred installation directory (defaults to `%LOCALAPPDATA%\UEQuest by E`).
3. Configure options for Desktop shortcut (`Ultimate Quest` on homescreen) or Start Menu shortcuts.
4. Click **Install Now**. The installer will extract all files into `<Destination>\UEQuest by E\` and create shortcuts pointing to your desktop.

---

## Project Structure

```
Ultimate_Quest_by_Enan/
├── UltimateQuestbyENAN.py      # Core application builder & embedded source
├── setup_installer.py          # Full setup installer with uninstaller
├── build_setup.py              # Full installer compilation script
├── setup_installer_light.py    # Lightweight LZMA2 compact setup installer
├── build_setup_light.py        # Lightweight installer compilation script
├── build_cs_updater.py         # Standalone lightweight updater compiler (<10 MB)
├── uninstaller.py              # Standalone UEQ Uninstaller source code
├── Requirements.txt            # Python dependencies
├── README.md                   # Documentation
└── Ultimate_Quest_Folder/      # Output application folder
    ├── Ultimate_Quest.exe      # Main executable
    ├── UEQ Uninstaller.exe     # Uninstaller application
    └── _internal/             # Bundled libraries & timer.exe
```

---

## License

MIT License
