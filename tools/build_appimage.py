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
"""Build a single-file AppImage from the PyInstaller onedir bundle.

What is an AppImage, in one sentence? A *type-2* AppImage is a small runtime
(bootloader) prepended to a SquashFS image that contains an **AppDir**. At run
time the runtime mounts that SquashFS and executes ``AppRun``; nothing gets
installed. So the whole job here is:

    dist/GreenCrypt/            (PyInstaller onedir bundle, from `make standalone`)
        -> build/appimage/GreenCrypt.AppDir/     (AppDir layout)
        -> dist/GreenCrypt-x86_64.AppImage        (runtime + SquashFS)

The AppDir we assemble looks like this::

    GreenCrypt.AppDir/
    |-- AppRun                 # executable entry point (we ship packaging/AppRun)
    |-- greencrypt.desktop      # desktop entry (integration: menu, icon)
    |-- greencrypt.png          # icon referenced by Icon=greencrypt
    |-- .DirIcon -> greencrypt.png
    `-- usr/
        `-- bin/
            |-- greencrypt      # the frozen executable
            `-- _internal/      # its payload (Python, Qt, Cryptodome, data)

Run it with::

    python tools/build_appimage.py          # or: make appimage
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# --- Layout ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
BUNDLE = DIST / "GreenCrypt"                       # PyInstaller onedir output
APPDIR = BUILD / "appimage" / "GreenCrypt.AppDir"  # throwaway AppDir
TOOLS = BUILD / "tools"                            # downloaded helpers (ignored)

# --- appimagetool: the official tool that turns an AppDir into an AppImage --
# The continuous build is a static AppImage itself, so we just download, verify
# and run it. Each pinned entry is (sha256, size in bytes) of the exact artifact
# we tested against (build 313); a tampered or truncated download is rejected
# *before* we ever execute it.
APPIMAGETOOL_ARTIFACTS = {
    "x86_64": (
        "95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6",
        15092216,
    ),
    "aarch64": (
        "a595ea34cd6136c7f595e9dcbb16f3e9725d7610efb9e43b38c3c6e86cafc270",
        14678536,
    ),
}
_ARCH_MAP = {"x86_64": "x86_64", "aarch64": "aarch64", "armv7l": "armhf", "i686": "i686"}

# Timeout (seconds) for the appimagetool download — applies per blocking socket
# operation, so a stalled mirror cannot hang the build forever.
_DOWNLOAD_TIMEOUT = 60

# Substrings that reveal a *missing/broken FUSE* failure, which is the single
# recoverable case (as opposed to a genuine appimagetool error).
_FUSE_FAILURE_MARKERS = (
    "libfuse.so",      # dlopen(): error loading libfuse.so.2
    "require fuse",    # "AppImages require FUSE to run."
    "cannot mount",    # generic mount failure
    "fusermount",      # fusermount missing / failed
)


def _arch() -> str:
    """Map the host CPU to an AppImage architecture name."""
    machine = platform.machine()
    if machine not in _ARCH_MAP:
        sys.exit(f"error: unsupported architecture '{machine}' for AppImage builds")
    return _ARCH_MAP[machine]


def _chmod_x(path: Path) -> None:
    """Make a file executable (owner/group/other), preserving the rest."""
    path.chmod(path.stat().st_mode | 0o111)


# --- Step 1: make sure the bundle exists -----------------------------------
def ensure_bundle() -> None:
    exe = BUNDLE / "greencrypt"
    if not exe.is_file():
        sys.exit(
            "error: PyInstaller bundle not found at "
            f"{BUNDLE}\n       run 'make standalone' first."
        )


# --- Step 2: assemble the AppDir -------------------------------------------
def assemble_appdir() -> None:
    """Lay out a fresh AppDir from the bundle plus our packaging assets."""
    if APPDIR.exists():
        shutil.rmtree(APPDIR)
    bin_dir = APPDIR / "usr" / "bin"
    bin_dir.mkdir(parents=True)

    # The frozen bundle goes verbatim into usr/bin/. Keeping `greencrypt` and
    # `_internal/` as siblings is required: the PyInstaller bootloader locates
    # its payload relative to the executable's own path.
    shutil.copytree(BUNDLE, bin_dir, dirs_exist_ok=True)

    # AppRun (entry point) — must be executable.
    apprun = APPDIR / "AppRun"
    shutil.copy2(ROOT / "packaging" / "AppRun", apprun)
    _chmod_x(apprun)

    # Desktop entry (integration metadata). Its basename is irrelevant, but it
    # must sit at the AppDir root and define an Icon= we can satisfy.
    shutil.copy2(ROOT / "packaging" / "greencrypt.desktop", APPDIR / "greencrypt.desktop")

    # Icon: appimagetool looks for `<Icon>.png` at the AppDir root and also for
    # a `.DirIcon` (the thumbnail the file manager shows).
    icon_src = ROOT / "greencrypt" / "gui" / "assets" / "icon.png"
    shutil.copy2(icon_src, APPDIR / "greencrypt.png")
    shutil.copy2(icon_src, APPDIR / ".DirIcon")


# --- Step 3: fetch appimagetool (verified) ---------------------------------
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, dest: Path, expected_size: int | None) -> None:
    """Stream ``url`` into ``dest`` with a timeout and an optional size check.

    We deliberately avoid ``urllib.request.urlretrieve``: it has **no timeout**
    and cannot verify the size, so a stalled mirror would hang the build forever
    and a truncated transfer would slip through. Here we bail out both on a
    Content-Length mismatch (before writing) and on the final file size.
    """
    try:
        with urllib.request.urlopen(url, timeout=_DOWNLOAD_TIMEOUT) as response:
            declared = response.headers.get("Content-Length")
            if expected_size is not None and declared is not None and int(declared) != expected_size:
                sys.exit(f"error: {url} reports {declared} bytes, expected {expected_size}")
            with dest.open("wb") as out:
                # `length` here is the *buffer* size, not a limit on the total.
                shutil.copyfileobj(response, out, length=1024 * 1024)
    except OSError as exc:  # URLError, TimeoutError, connection resets...
        dest.unlink(missing_ok=True)
        sys.exit(f"error: download failed ({url}): {exc}")

    if expected_size is not None:
        got = dest.stat().st_size
        if got != expected_size:
            dest.unlink(missing_ok=True)
            sys.exit(f"error: size mismatch for {dest.name}: got {got}, expected {expected_size}")


def ensure_appimagetool(arch: str) -> Path:
    """Download + verify appimagetool, or reuse a cached, already-verified copy."""
    tool = TOOLS / f"appimagetool-{arch}.AppImage"
    pinned = APPIMAGETOOL_ARTIFACTS.get(arch)
    expected_sha, expected_size = pinned if pinned else (None, None)

    # Cache hit: reuse without re-downloading (this is why rebuilds are fast).
    if tool.is_file() and (expected_sha is None or _sha256(tool) == expected_sha):
        return tool

    if expected_sha is None:
        print(f"[!] no pinned checksum for '{arch}'; the download will NOT be verified")

    TOOLS.mkdir(parents=True, exist_ok=True)
    url = (
        "https://github.com/AppImage/appimagetool/releases/download/continuous/"
        f"appimagetool-{arch}.AppImage"
    )
    print(f"[*] Downloading appimagetool ({arch}) ...")
    _download(url, tool, expected_size)

    if expected_sha is not None:
        got = _sha256(tool)
        if got != expected_sha:
            tool.unlink(missing_ok=True)
            sys.exit(f"error: sha256 mismatch for appimagetool\n  expected {expected_sha}\n  got      {got}")

    _chmod_x(tool)
    return tool


# --- Step 4: run appimagetool ----------------------------------------------
def _looks_like_fuse_failure(log: str) -> bool:
    """True only when the log shows a missing/broken FUSE — the recoverable case."""
    lowered = log.lower()
    return any(marker in lowered for marker in _FUSE_FAILURE_MARKERS)


def _run_appimagetool(
    tool: Path, args: list[str], env: dict[str, str]
) -> subprocess.CompletedProcess:
    """Run appimagetool, echo its combined log, and return the finished process."""
    cmd = [str(tool), *args]
    print("$ " + " ".join(cmd))
    proc = subprocess.run(
        cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if proc.stdout:
        print(proc.stdout, end="")
    return proc


def build_appimage(tool: Path, arch: str) -> Path:
    output = DIST / f"GreenCrypt-{arch}.AppImage"
    output.unlink(missing_ok=True)

    env = {**os.environ, "ARCH": arch}  # appimagetool reads ARCH from the env
    proc = _run_appimagetool(tool, [str(APPDIR), str(output)], env)
    if proc.returncode == 0:
        return output

    # Only a missing FUSE is recoverable, and only that one we work around. Any
    # other error is real: surface it instead of blindly retrying (which is what
    # a bare `except CalledProcessError` used to do).
    if _looks_like_fuse_failure(proc.stdout or ""):
        print("[!] FUSE unavailable; retrying with --appimage-extract-and-run ...")
        retry = _run_appimagetool(
            tool, ["--appimage-extract-and-run", str(APPDIR), str(output)], env
        )
        if retry.returncode == 0:
            return output
        sys.exit("error: appimagetool failed even with --appimage-extract-and-run")

    sys.exit(f"error: appimagetool failed (exit code {proc.returncode})")


def main() -> int:
    arch = _arch()
    ensure_bundle()
    assemble_appdir()
    tool = ensure_appimagetool(arch)
    output = build_appimage(tool, arch)

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"\n[+] AppImage built: {output} ({size_mb:.1f} MB)")
    print(f"    run it:  ./{output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
