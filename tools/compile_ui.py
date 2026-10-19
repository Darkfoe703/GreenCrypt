#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# GreenCrypt — AES-256-EAX file & folder encryption tool.
# Copyright (C) 2026  Marco Antonio Romero (@Darkfoe703)
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Contact:
#   Email:    marcoromero.dev@gmail.com
#   Telegram: @Darkfoe703
#
"""
Compile the Qt Designer UI into the Python module imported by the GUI.

    greencrypt/gui/main.ui  --(pyside6-uic)-->  greencrypt/gui/main_ui.py

``main.ui`` is the **single source of truth**. ``main_ui.py`` is *generated*
but is **committed** on purpose, so a fresh clone (and ``pip install '.[gui]'``)
works without the user having to run a compiler.

Never edit ``main_ui.py`` by hand — edit ``main.ui`` and run this script.

Usage
-----
    python tools/compile_ui.py            # regenerate main_ui.py in place
    python tools/compile_ui.py --check    # exit 1 if main_ui.py is out of date

The ``--check`` mode is meant for CI / pre-commit: it regenerates into a
temporary file and compares, so it never touches the working tree.
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Repository root = parent of this file's directory (tools/).
ROOT = Path(__file__).resolve().parent.parent
UI_FILE = ROOT / "greencrypt" / "gui" / "main.ui"
OUT_FILE = ROOT / "greencrypt" / "gui" / "main_ui.py"


def find_uic() -> list[str] | None:
    """Locate ``pyside6-uic`` and return the argv prefix used to run it.

    Search order:
      1. next to the running interpreter (covers the in-repo virtualenv),
      2. ``$PATH``.
    Returns ``None`` when the compiler is not installed.
    """
    exe = "pyside6-uic.exe" if os.name == "nt" else "pyside6-uic"
    scripts_dir = "Scripts" if os.name == "nt" else "bin"

    candidates = [
        Path(sys.executable).resolve().parent / exe,  # <venv>/bin/pyside6-uic
        Path(sys.prefix) / scripts_dir / exe,  # robust on Windows
    ]
    for candidate in candidates:
        if candidate.is_file():
            return [str(candidate)]

    found = shutil.which("pyside6-uic")  # anywhere on PATH
    if found:
        return [found]

    return None


def run_uic(uic: list[str], output: Path) -> None:
    """Run the UI compiler, reading ``main.ui`` and writing ``output``."""
    command = [*uic, str(UI_FILE), "-o", str(output)]
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompile greencrypt/gui/main_ui.py from main.ui.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify main_ui.py is up to date; exit 1 on drift (writes nothing)",
    )
    args = parser.parse_args()

    if not UI_FILE.is_file():
        print(f"[!] UI source not found: {UI_FILE}", file=sys.stderr)
        return 2

    uic = find_uic()
    if uic is None:
        print("[!] Could not find 'pyside6-uic'.", file=sys.stderr)
        print("    Install it with:  pip install pyside6", file=sys.stderr)
        return 2

    # --- Check mode: regenerate to a temp file and compare (no tree changes) --
    if args.check:
        tmp = OUT_FILE.with_name(OUT_FILE.name + ".check")
        try:
            run_uic(uic, tmp)
            up_to_date = OUT_FILE.is_file() and filecmp.cmp(OUT_FILE, tmp, shallow=False)
        finally:
            tmp.unlink(missing_ok=True)

        if up_to_date:
            print(f"[ok] {OUT_FILE.relative_to(ROOT)} is up to date with {UI_FILE.name}.")
            return 0
        print(
            f"[!] {OUT_FILE.relative_to(ROOT)} is OUT OF DATE with {UI_FILE.name}.", file=sys.stderr
        )
        print("    Run:  make ui   (or: python tools/compile_ui.py)", file=sys.stderr)
        return 1

    # --- Normal mode: regenerate in place -------------------------------------
    run_uic(uic, OUT_FILE)
    print(f"[ok] Regenerated {OUT_FILE.relative_to(ROOT)} from {UI_FILE.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
