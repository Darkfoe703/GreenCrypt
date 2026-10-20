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
Frozen-application entry point (used as PyInstaller's analysis root).

PyInstaller needs a plain script to start from. This one just calls the same
dispatcher as the installed ``greencrypt`` console script:

    * no arguments   -> launch the Qt GUI
    * with arguments -> run the command-line interface

Keeping it as its own file (instead of freezing ``GCrypt.py``) makes the bundling
intent explicit and decoupled from the compatibility shim at the repo root.
"""

from greencrypt.cli import main

if __name__ == "__main__":
    main()
