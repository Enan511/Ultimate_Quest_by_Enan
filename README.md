# Ultimate Quest (Revised)

A PySide6 desktop application that manages game launches for Discord Orb Quests. Features standard game executable spoofing, **Steam Quest Mode** with fake `appmanifest_<appid>.acf` generation, lightweight countdown timers (~12.4 MB), embedded custom icons, and a standalone PySide6 Setup Installer.

---

## Key Features

- **Standard Quest Spoofing** — Add games via bulk text input or sync with remote Gist quest lists.
- **Steam Quest Mode** — Real-time Steam Store search (`store.steampowered.com/api/storesearch/`) and SteamCMD API metadata extraction. Automatically generates fake `appmanifest_<appid>.acf` files (`StateFlags 1026`) in `Steam/steamapps/` for advanced quest validation (e.g. *Marathon*, *Toxic Commando Demo*).
- **Morphing Card UI** — PySide6 `QStackedWidget` interface cleanly toggles between Standard Mode and Steam Mode views without UI clutter.
- **Lightweight Countdown Timer** — Compiles a Tkinter timer executable (`timer.exe`) with a teal dark-mode theme.
- **Interactive Manual Exit Protocol** — Custom confirmation popup (*"Do you want to delete game files upon closing?"*) with **Yes** and **No** controls, plus an `"Ask every time before closing"` preference toggle inside the timer window.
- **Dynamic C# Self-Deletion** — Timer compiles a silent windowless C# binary (`deleter.exe`) via Windows' built-in `csc.exe` to handle post-exit file, folder, icon, and manifest cleanup.
- **VirusTotal Safe Folder Build** — Compiles as an un-compressed directory package (`--onedir`), eliminating generic heuristic dropper/unpacking false positive flags.
- **Standalone Setup Installer Builder** — Includes `setup_installer.py` and `build_setup.py` to create `Ultimate_Quest_Setup.exe` with custom directory selection (installs into a `UEQuest by E` folder) and Windows Desktop/Start Menu shortcut creation.

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

This will:
1. Compile the Tkinter timer into `timer.exe`.
2. Bundle custom icon assets (`UQ.ico`, `Steam.ico`, `Jett.ico`, `Ahri.ico`, etc.).
3. Compile the main PySide6 application into `Ultimate_Quest_Folder/` (containing `Ultimate_Quest.exe`).

### Step 2: Build the Setup Installer Executable

Run the setup builder script:

```bash
python build_setup.py
```

This bundles `Ultimate_Quest_Folder` into a standalone installer: **`Ultimate_Quest_Setup.exe`**.

---

## Installation & Setup

1. Double-click `Ultimate_Quest_Setup.exe`.
2. Select your preferred installation directory (defaults to `%LOCALAPPDATA%\UEQuest by E`).
3. Toggle options for Desktop or Start Menu shortcuts.
4. Click **Install Now**. The installer will extract all files into `<Destination>\UEQuest by E\` and create shortcuts pointing to your desktop.

---

## Project Structure

```
Ultimate_Quest_Revised/
├── UltimateQuestbyENAN.py   # Core builder script & embedded source code
├── setup_installer.py       # PySide6 Setup Installer application
├── build_setup.py           # Installer packaging script
├── Requirements.txt         # Dependencies
├── README.md                # Documentation
└── Ultimate_Quest_Folder/   # Output application folder
    ├── Ultimate_Quest.exe   # Main executable
    └── _internal/          # Bundled libraries & timer.exe
```

---

## License

MIT License
