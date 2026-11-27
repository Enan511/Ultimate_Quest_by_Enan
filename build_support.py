"""Keep Windows runtime dependencies consistent across PyInstaller builds."""

import importlib.util
import os
import shutil
from pathlib import Path


def qt_runtime_files():
    """Use the C++ runtime distributed with the installed Shiboken wheel."""
    spec = importlib.util.find_spec("shiboken6")
    if spec is None or spec.origin is None:
        raise RuntimeError("Install the project requirements before building Ultimate Quest.")

    wheel = Path(spec.origin).parent
    files = {dll.name.lower(): dll for dll in wheel.glob("*.dll")
             if dll.name.lower().startswith(("msvcp140", "vcruntime140", "concrt140"))}
    required = {"msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"}
    if missing := required - files.keys():
        raise RuntimeError(f"The Shiboken wheel is missing Windows runtime files: {', '.join(sorted(missing))}")
    return sorted(files.values())


def runtime_binary_args(files):
    args = []
    for dll in files:
        args.extend(("--add-binary", f"{dll}{os.pathsep}."))
    return args


def stage_app_runtime(files, directory):
    """Give the installed app a local runtime in Windows' application directory."""
    app_dir = Path(directory)
    for dll in files:
        shutil.copy2(dll, app_dir / dll.name)
        shutil.copy2(dll, app_dir / "_internal" / dll.name)


def pyinstaller_environment():
    """Keep unrelated ICU installations on PATH out of the Windows bundle."""
    env = os.environ.copy()
    system32 = Path(env.get("SystemRoot", r"C:\Windows")) / "System32"
    paths = [Path(path.strip('"')) for path in env.get("PATH", "").split(os.pathsep) if path]
    env["PATH"] = os.pathsep.join(str(path) for path in paths
                                  if path == system32 or not (path / "icuuc.dll").is_file())
    return env
