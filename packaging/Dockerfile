# GreenCrypt — AES-256-EAX file & folder encryption tool.
# Copyright (C) 2026  Marco Antonio Romero (@Darkfoe703)
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Build environment for a *maximally portable* Linux AppImage.
#
# Why a container at all?
#   PyInstaller freezes the interpreter of the machine that runs it, so the
#   resulting AppImage can never be more portable than that machine's glibc
#   (glibc is forward-, NOT backward-compatible). Building on a modern host
#   produces an AppImage that dies on older distros with, e.g.,
#       "GLIBC_2.38 not found".
#
# Why manylinux_2_34 (and not 2_28)?
#   PySide6 6.12 only ships `manylinux_2_34` wheels for x86_64, which require
#   glibc >= 2.34 and libstdc++ GLIBCXX_3.4.29. manylinux_2_28 (glibc 2.28)
#   can neither install nor run them. manylinux_2_34 == AlmaLinux 9 brings
#   exactly glibc 2.34 and a system libstdc++ with GLIBCXX_3.4.29 (GCC 11) —
#   the lowest floor PySide6 allows.
#
# Result: the AppImage runs on Ubuntu 22.04+, Debian 12+, RHEL/Rocky 9+,
# Linux Mint 21+, Fedora 35+, ... (anything with glibc >= 2.34).
#
# Usage: `make appimage-docker` (the image only compiles; the source tree is
# bind-mounted at run time, so you rarely need to rebuild the image).
FROM quay.io/pypa/manylinux_2_34_x86_64@sha256:3a7a51dd9c82f9e0b81e5cf72fd7e784906d76fcec727dd1645f609c869289fa

ENV VENV=/opt/gc-venv \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System Python 3.12 (a proper shared-library build) + helpers.
#   - ca-certificates: our build script downloads appimagetool over HTTPS.
#   - findutils/file:   post-build sanity checks.
# NOTE: the CPythons under manylinux's /opt/python are built *without*
# `--enable-shared`, so PyInstaller refuses them; the distro interpreter works.
RUN dnf install -y ca-certificates findutils file python3.12 && dnf clean all

# PyInstaller locates libpython through sysconfig. RHEL's python3.12 reports
# `Py_ENABLE_SHARED=0` (its executable is statically linked against libpython),
# but it *does* ship the shared library. PyInstaller then falls back to looking
# for `libpython3.12.so.1.0` in `base_prefix` and `base_prefix/lib` (= /usr and
# /usr/lib) — yet on RHEL the library lives in /usr/lib64. Expose it where
# PyInstaller expects to find it.
RUN ln -sf /usr/lib64/libpython3.12.so.1.0 /usr/lib/libpython3.12.so.1.0

# An isolated virtualenv, outside the (bind-mounted) source tree.
RUN /usr/bin/python3.12 -m venv "${VENV}" \
 && "${VENV}/bin/pip" install --upgrade pip

# Runtime deps of the GUI app + the freezer. Mirrors pyproject.toml:
#   [project.dependencies]              -> pycryptodomex
#   [project.optional-dependencies].gui -> PySide6
#   [dependency-groups].package         -> pyinstaller
RUN "${VENV}/bin/pip" install \
      "pycryptodomex>=3.20" \
      "PySide6>=6.5" \
      "pyinstaller>=6.10"

WORKDIR /src
CMD ["bash"]
