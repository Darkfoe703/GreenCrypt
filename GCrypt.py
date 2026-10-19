#!/usr/bin/env python
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
GCrypt.py — backward-compatible launcher for GreenCrypt.

The implementation was refactored into the importable ``greencrypt`` package:

    greencrypt.core   -- crypto + .aes format (UI-agnostic)
    greencrypt.cli    -- command line, interactive menu, GUI launcher
    greencrypt.gui    -- Qt front-end

This file is intentionally a tiny shim so that the historical invocation keeps
working unchanged::

    python GCrypt.py                 # GUI (no args)
    python GCrypt.py -i              # interactive CLI menu
    python GCrypt.py -e -p s file    # pure CLI

Preferred forms going forward::

    python -m greencrypt [args...]   # run straight from the source tree
    greencrypt [args...]             # after `pip install .`
"""

import sys

from greencrypt.cli import main

if __name__ == "__main__":
    main()
