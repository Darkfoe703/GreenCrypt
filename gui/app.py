#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GreenCrypt GUI — Qt front-end for the GCrypt crypto core.

Prerequisites
-------------
1. Install PySide6 in your virtualenv:
       pip install pyside6
2. Compile the Qt Designer UI into a Python module:
       pyside6-uic gui/main.ui -o gui/main_ui.py
3. Run:
       python gui/app.py

The module reuses the exact crypto logic from the repository root (GCrypt.py):
same file format, same PBKDF2-HMAC-SHA256 derivation, same AEAD filename
authentication. No crypto is re-implemented here.

All user-facing strings are in English.
"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QMenu,
)

# --- Import the crypto core from the repository root --------------------------
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from GCrypt import (  # noqa: E402
    encrypt_file,
    decrypt_file,
    scan_dir,
    GreenCryptError,
    EXT,
)

# --- Import the generated UI module (must be compiled first) -------------------
try:
    from main_ui import Ui_MainWindow  # type: ignore
except ImportError:
    sys.stderr.write(
        "\nERROR: 'gui/main_ui.py' was not found.\n"
        "Compile the UI first with:\n"
        "    pyside6-uic gui/main.ui -o gui/main_ui.py\n\n"
    )
    raise


# Keep in sync with the default text defined in gui/main.ui
DEFAULT_HINT = 'Drag files or folders here'

# Folder that holds optional visual assets (logo, window icon).
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# Icon file names tried, in order. PNG works at runtime on every OS; ICO is
# handy on Windows and ICNS on macOS if you ship one.
ICON_CANDIDATES = ("icon.png", "icon.ico", "icon.icns", "logo.png")

# Drop-zone styling: a dark backdrop keeps the white hint readable even when
# no logo image is available.
DROP_STYLE = (
    "QFrame#dropFrame { background-color: #2b2b2b;"
    " border: 2px dashed #777777; border-radius: 8px; }"
)
DROP_STYLE_ACTIVE = (
    "QFrame#dropFrame { background-color: #2b2b2b;"
    " border: 2px dashed #4caf50; border-radius: 8px; }"
)

# Maximum number of file names shown inside the drop area
MAX_NAMES = 5


def load_app_icon():
    """Return the window/application icon, or None when no icon file exists.

    Qt picks a suitable size from the file; a 256x256 PNG is a good default.
    """
    for name in ICON_CANDIDATES:
        path = ASSETS_DIR / name
        if path.is_file():
            return QIcon(str(path))
    return None


def installed_desktop_file(app_id):
    """Return the path of an installed ``<app_id>.desktop`` launcher, or None.

    We only announce the app id to the desktop portal (setDesktopFileName)
    when a matching launcher is really installed. Otherwise Wayland/Qt logs:

        qt.qpa.services: Failed to register with host portal ...
        "Could not register app ID: App info not found for 'greencrypt'"

    Looks in $XDG_DATA_HOME/applications and $XDG_DATA_DIRS/applications.
    """
    filename = f"{app_id}.desktop"
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    for base in (data_home, *data_dirs.split(":")):
        if base and (Path(base) / "applications" / filename).is_file():
            return Path(base) / "applications" / filename
    return None


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main application window wired to the GCrypt core."""

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # --- Internal state ---------------------------------------------------
        self.targets = []          # list[str]: absolute paths queued for processing
        self.password_file = None  # str | None: path to a password file

        # --- Cosmetic / behavior setup ---------------------------------------
        self._configure_drop_area()
        self._load_logo()
        self._connect_signals()

        self._refresh_targets()
        self.lblStatus.setText("Ready")

    # ------------------------------------------------------------------ setup
    def _configure_drop_area(self):
        """Make the whole frame (and its overlay children) accept drag & drop."""
        self.dropFrame.setStyleSheet(DROP_STYLE)

        # The logo and the hint label cover the frame, so enable drops on them
        # too and intercept all drag events centrally via an event filter.
        for widget in (self.dropFrame, self.lblLogo, self.lblDropHint):
            widget.setAcceptDrops(True)
            widget.installEventFilter(self)

        # Right-click on the drop area -> clear the current selection
        self.dropFrame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dropFrame.customContextMenuRequested.connect(self._on_drop_context_menu)

    def _load_logo(self):
        """Load a logo into lblLogo if one exists; otherwise leave it empty."""
        candidates = [
            ASSETS_DIR / "logo.png",
            ASSETS_DIR / "logo.jpg",
            Path(__file__).resolve().parent / "logo.png",
        ]
        for path in candidates:
            if path.is_file():
                self.lblLogo.setPixmap(QPixmap(str(path)))
                return
        # No logo found: the dark drop-zone background shows through.

    def _connect_signals(self):
        """Connect widgets (from the .ui) to our handlers."""
        self.btnBrowse.clicked.connect(self.on_browse)
        self.btnEncrypt.clicked.connect(self.on_encrypt)
        self.btnDecrypt.clicked.connect(self.on_decrypt)
        self.chkUsePasswordFile.toggled.connect(self._on_use_password_file_toggled)

        # Menu actions
        self.actionOpenFiles.triggered.connect(self.on_browse_files)
        self.actionOpenFolder.triggered.connect(self.on_browse_folder)
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.on_about)

    # ------------------------------------------------------------ drag & drop
    def eventFilter(self, obj, event):
        """Intercept drag & drop events coming from the frame or its children."""
        if obj in (self.dropFrame, self.lblLogo, self.lblDropHint):
            etype = event.type()
            if etype == QEvent.Type.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    self.dropFrame.setStyleSheet(DROP_STYLE_ACTIVE)
                    return True
            elif etype == QEvent.Type.DragMove:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif etype == QEvent.Type.DragLeave:
                self.dropFrame.setStyleSheet(DROP_STYLE)
                return True
            elif etype == QEvent.Type.Drop:
                self.dropFrame.setStyleSheet(DROP_STYLE)
                self._on_drop(event)
                return True
        return super().eventFilter(obj, event)

    def _on_drop(self, event):
        urls = event.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        self.add_targets(paths)
        event.acceptProposedAction()

    def _on_drop_context_menu(self, pos):
        menu = QMenu(self)
        clear_action = menu.addAction("Clear selection")
        clear_action.setEnabled(bool(self.targets))
        chosen = menu.exec(self.dropFrame.mapToGlobal(pos))
        if chosen is clear_action:
            self.targets.clear()
            self._refresh_targets()
            self.lblStatus.setText("Selection cleared.")

    # -------------------------------------------------------- target management
    def add_targets(self, paths):
        """Add unique, existing paths to the queue and refresh the display."""
        added = 0
        for p in paths:
            if not p:
                continue
            ap = os.path.abspath(p)
            if os.path.exists(ap) and ap not in self.targets:
                self.targets.append(ap)
                added += 1
        if added:
            self.lblStatus.setText(f"Added {added} item(s).")
        else:
            self.lblStatus.setText("No new items were added.")
        self._refresh_targets()

    def _refresh_targets(self):
        """Show a summary of the queued items inside the drop area."""
        n = len(self.targets)
        if n == 0:
            self.lblDropHint.setText(DEFAULT_HINT)
            return

        names = [os.path.basename(p.rstrip("/\\")) or p for p in self.targets]
        shown = names[:MAX_NAMES]
        text = f"{n} item(s) selected\n" + "\n".join(shown)
        if n > MAX_NAMES:
            text += f"\n... and {n - MAX_NAMES} more"
        self.lblDropHint.setText(text)

    # ------------------------------------------------------------- browse
    def on_browse(self):
        """Ask the user whether to add files or a folder."""
        box = QMessageBox(self)
        box.setWindowTitle("Add items")
        box.setText("What would you like to add?")
        files_btn = box.addButton("Files...", QMessageBox.ButtonRole.AcceptRole)
        folder_btn = box.addButton("Folder...", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is files_btn:
            self.on_browse_files()
        elif clicked is folder_btn:
            self.on_browse_folder()

    def on_browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files")
        if paths:
            self.add_targets(paths)

    def on_browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select folder")
        if path:
            self.add_targets([path])

    # ----------------------------------------------------------- password files
    def _on_use_password_file_toggled(self, checked):
        if checked:
            path, _ = QFileDialog.getOpenFileName(self, "Select password file")
            if not path:
                # User cancelled -> revert the checkbox
                self.chkUsePasswordFile.setChecked(False)
                return
            self.password_file = path
            self.txtPwd1.setEnabled(False)
            self.txtPwd2.setEnabled(False)
            self.lblStatus.setText(f"Password file: {os.path.basename(path)}")
        else:
            self.password_file = None
            self.txtPwd1.setEnabled(True)
            self.txtPwd2.setEnabled(True)
            self.lblStatus.setText("Ready")

    def _read_password_file(self, path):
        """Read the password from the first line (no sys.exit, GUI-safe)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                pw = f.readline().strip()
        except OSError as e:
            raise GreenCryptError(f"Cannot read password file: {e}") from e
        if not pw:
            raise GreenCryptError("The password file is empty.")
        return pw

    def _resolve_password(self):
        """Return the password from the fields or the password file."""
        if self.chkUsePasswordFile.isChecked():
            if not self.password_file:
                raise GreenCryptError("No password file selected.")
            return self._read_password_file(self.password_file)

        p1 = self.txtPwd1.text()
        p2 = self.txtPwd2.text()
        if not p1:
            raise GreenCryptError("Please enter a password.")
        if p1 != p2:
            raise GreenCryptError("Passwords do not match.")
        return p1

    # ------------------------------------------------------------- actions
    def on_encrypt(self):
        self._run(mode="enc")

    def on_decrypt(self):
        self._run(mode="dec")

    def _run(self, mode):
        """Shared worker for both encrypt (mode='enc') and decrypt (mode='dec')."""
        if not self.targets:
            QMessageBox.information(
                self,
                "No selection",
                "Add files or folders first (drag & drop or use Browse...).",
            )
            return

        # 1. Resolve password
        try:
            password = self._resolve_password()
        except GreenCryptError as e:
            QMessageBox.warning(self, "Password", str(e))
            return

        delete = self.chkDeleteOriginal.isChecked()

        # 2. Expand the selection into a flat list of files
        files = self._collect_files(mode)
        if not files:
            QMessageBox.information(
                self,
                "Nothing to do",
                "No matching files were found in the selection.",
            )
            return

        # 3. Process with a per-file progress bar
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, len(files))
        self.progressBar.setValue(0)

        ok = 0
        errors = []
        for i, f in enumerate(files, start=1):
            try:
                if mode == "enc":
                    encrypt_file(password, f, delete_original=delete)
                else:
                    decrypt_file(password, f, delete_original=delete)
                ok += 1
            except GreenCryptError as e:
                errors.append(f"{os.path.basename(f)}: {e}")
            except ValueError as e:
                # Raised by the AEAD on a MAC/format failure
                errors.append(f"{os.path.basename(f)}: {e}")

            self.progressBar.setValue(i)
            self.lblStatus.setText(f"Processing {i}/{len(files)}...")
            QApplication.processEvents()  # keep the UI responsive

        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)

        verb = "Encrypted" if mode == "enc" else "Decrypted"
        self.lblStatus.setText(f"{verb} {ok}/{len(files)} file(s).")

        if errors:
            details = "\n".join(errors[:10])
            if len(errors) > 10:
                details += f"\n... and {len(errors) - 10} more"
            QMessageBox.warning(
                self,
                "Completed with errors",
                f"{verb} {ok} of {len(files)} file(s).\n\nErrors:\n{details}",
            )
        else:
            QMessageBox.information(self, "Done", f"{verb} {ok} file(s).")
            # Tidy up on full success
            self.targets.clear()
            self._refresh_targets()

    def _collect_files(self, mode):
        """Flatten targets into concrete files depending on the operation."""
        files = []
        for t in self.targets:
            if os.path.isfile(t):
                files.append(t)
            elif os.path.isdir(t):
                if mode == "enc":
                    files.extend(scan_dir(t))
                else:
                    files.extend(f for f in scan_dir(t) if f.endswith(EXT))
        return files

    # ---------------------------------------------------------------- dialogs
    def on_about(self):
        QMessageBox.about(
            self,
            "About GreenCrypt",
            "<b>GreenCrypt</b><br>"
            "AES-256-EAX file &amp; folder encryption tool.<br><br>"
            "Format v1 — PBKDF2-HMAC-SHA256 (200,000 iterations)<br>"
            "Filename authenticated through AEAD (associated data).<br><br>"
            "Shared core with the CLI (<code>GCrypt.py</code>).",
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GreenCrypt")
    # Linux/KDE/Wayland: only announce the app id when a greencrypt.desktop
    # launcher is installed, so the window groups with it and shows the right
    # icon. Setting it without a launcher makes the portal log a warning.
    if installed_desktop_file("greencrypt") is not None:
        app.setDesktopFileName("greencrypt")
    app.setStyle("Fusion")  # consistent look across Linux/Windows

    # Window icon: app.setWindowIcon covers every window and dialog by default.
    icon = load_app_icon()
    if icon is not None:
        app.setWindowIcon(icon)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
