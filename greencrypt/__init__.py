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
GreenCrypt
==========

AES-256-EAX file & folder encryption tool with two front-ends:

* :mod:`greencrypt.cli` — command line + interactive menu,
* :mod:`greencrypt.gui` — Qt desktop application.

The cryptography core (:mod:`greencrypt.core`) is UI-agnostic and is also
re-exported here for convenience::

    from greencrypt import encrypt_file, decrypt_file

Running the package directly::

    python -m greencrypt          # GUI when no args, CLI otherwise
    python -m greencrypt -i       # interactive menu
"""

from __future__ import annotations

# Single source of truth for the project version.
# ``pyproject.toml`` mirrors this value; keep them in sync.
__version__ = "1.0.0"

# Re-export the public core API so callers can simply do
# ``from greencrypt import encrypt_file``.
from .core import (  # noqa: F401
    CURRENT_VERSION,
    EXT,
    MAGIC,
    GreenCryptError,
    decrypt_bytes,
    decrypt_file,
    decrypt_target,
    derive_key,
    encrypt_bytes,
    encrypt_file,
    encrypt_target,
    scan_dir,
)

__all__ = [
    "__version__",
    "CURRENT_VERSION",
    "EXT",
    "MAGIC",
    "GreenCryptError",
    "decrypt_bytes",
    "decrypt_file",
    "decrypt_target",
    "derive_key",
    "encrypt_bytes",
    "encrypt_file",
    "encrypt_target",
    "scan_dir",
]
