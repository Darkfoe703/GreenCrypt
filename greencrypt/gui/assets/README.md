# GreenCrypt GUI assets

Put the application logo here.

- Expected file name: **`logo.png`** (also tried: `logo.jpg`).
- It is loaded into the `lblLogo` label of `greencrypt/gui/main.ui`.
- The label uses `scaledContents=true`, so the image **stretches to fill** the
  whole drop area (it may distort if the aspect ratio does not match).
- Use a **dark** image (or one with a dark area in the middle) so the white
  hint text — "Drag files or folders here..." — stays readable on top.

If no logo is present, the drop area falls back to a plain dark background.

## Application icon

Drop an icon file in this same folder to give the app a window/taskbar icon.

- Preferred file name: **`icon.png`** (256x256 recommended).
- Also accepted, in this order: `icon.ico`, `icon.icns`, then `logo.png`.
- It is loaded by `load_app_icon()` in `greencrypt/gui/app.py` and applied with
  `app.setWindowIcon(...)`, which covers every window and dialog.

Notes per platform:

- **Linux (KDE/GNOME):** `app.setDesktopFileName("greencrypt")` is set, so the
  dock groups the window with a `greencrypt.desktop` launcher. To install one:
  create `~/.local/share/applications/greencrypt.desktop` with
  `Icon=/absolute/path/to/greencrypt/gui/assets/icon.png`.
- **Windows (.exe):** the icon inside a packaged binary comes from PyInstaller,
  e.g. `pyinstaller --icon=greencrypt/gui/assets/icon.ico --windowed greencrypt/gui/app.py`.
- **SVG:** not enabled by default (needs the Qt SVG plugin); use PNG instead.
