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
GreenCrypt — command-line front-end.

Responsibilities:

  * the ASCII banner,
  * the interactive menu (``-i``),
  * argument parsing and the pure CLI mode (``-e`` / ``-d``),
  * launching the Qt GUI when no arguments are given.

All cryptography lives in :mod:`greencrypt.core`; this module never touches
AES directly. Keeping I/O and crypto separate is what lets the same core power
both the CLI and the GUI.
"""

from __future__ import annotations

import argparse
import os
import sys

from .core import (
    GreenCryptError,
    decrypt_target,
    encrypt_target,
    password_from_file,
)


# -- Banner --------------------------------------------------------------------


def banner():
    green = "\033[1;32m"
    reset = "\033[m"
    print(
        green
        + r"""
   _____                      _____                  _   
  / ____|                    / ____|                | |  
 | |  __ _ __ ___  ___ _ __ | |     _ __ _   _ _ __ | |_ 
 | | |_ | '__/ _ \/ _ | '_ \| |    | '__| | | | '_ \| __|
 | |__| | | |  __|  __| | | | |____| |  | |_| | |_) | |_ 
  \_____|_|  \___|\___|_| |_|\_____|_|   \__, | .__/ \__|
                                          __/ | |        
                                         |___/|_|        
"""
        + reset
    )


# -- Interactive mode ----------------------------------------------------------


def interactive_mode():
    """Simple guided menu for people who prefer not to memorise flags."""
    banner()
    print("  1) Encrypt\n  2) Decrypt\n  3) Exit")
    choice = input("Select [1/2/3]: ").strip()
    if choice == "3":
        return
    if choice not in ("1", "2"):
        print("[!] Invalid choice.")
        return

    raw_target = input("File or folder path: ").strip()
    target = os.path.abspath(raw_target)
    if not os.path.exists(target):
        print(f"[!] '{target}' does not exist.")
        return

    password = input("Password: ")

    answer = input("Delete original after processing? [y/N]: ").strip().lower()
    delete = answer == "y"

    print()
    try:
        if choice == "1":
            encrypt_target(password, target, delete_original=delete)
        else:
            decrypt_target(password, target, delete_original=delete)
    except GreenCryptError as e:
        print(f"[!] Error: {e}")


# -- CLI argument parser -------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greencrypt",
        description="GreenCrypt — AES-256-EAX file/folder encryption",
        epilog=(
            "Examples:\n"
            "  %(prog)s                      launch the GUI\n"
            "  %(prog)s -i                   interactive CLI menu\n"
            "  %(prog)s -e -p 'secret' photo.jpg\n"
            "  %(prog)s -d -p 'secret' photo.jpg.aes\n"
            "  %(prog)s -e -f pass.txt documents/\n"
            "  %(prog)s -e -p 'secret' --delete secret.txt\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Action (mutually exclusive): encrypt / decrypt / interactive
    action_grp = parser.add_mutually_exclusive_group()
    action_grp.add_argument(
        "-e",
        "--encrypt",
        action="store_true",
        help="Encrypt the target file or folder",
    )
    action_grp.add_argument(
        "-d",
        "--decrypt",
        action="store_true",
        help="Decrypt the target file or folder",
    )
    action_grp.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run the interactive CLI menu (no GUI)",
    )

    # Password source (mutually exclusive)
    pwd_grp = parser.add_mutually_exclusive_group()
    pwd_grp.add_argument(
        "-p",
        "--password",
        metavar="PASSWORD",
        help="Password as a plain string",
    )
    pwd_grp.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        help="Path to a file containing the password (first line used)",
    )

    parser.add_argument(
        "target",
        nargs="?",
        metavar="TARGET",
        help="File or folder to encrypt/decrypt",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete the original file(s) after processing",
    )

    return parser


def cli_mode(args):
    """Non-interactive mode driven by command-line flags."""
    banner()

    # Validate action
    if not args.encrypt and not args.decrypt:
        print("[!] Specify -e (encrypt) or -d (decrypt).")
        sys.exit(1)

    # Validate target
    if not args.target:
        print("[!] You must specify a TARGET file or folder.")
        sys.exit(1)

    target = os.path.abspath(args.target)
    if not os.path.exists(target):
        print(f"[!] '{target}' does not exist.")
        sys.exit(1)

    # Resolve password + run. Everything that can go wrong raises
    # GreenCryptError, so a single try/except keeps the messages tidy.
    try:
        if args.password:
            password = args.password
            # Warn about password on CLI (visible in ps, history, logs)
            print(
                "[!] WARNING: Password provided via -p/--password is visible in process list and shell history."
            )
            print("    Consider using -f/--file or interactive input instead.")
        elif args.file:
            password = password_from_file(args.file)
        else:
            password = input("Password: ")

        print()
        if args.encrypt:
            encrypt_target(password, target, delete_original=args.delete)
        else:
            decrypt_target(password, target, delete_original=args.delete)
    except GreenCryptError as e:
        print(f"[!] Error: {e}")
        sys.exit(1)


# -- GUI launcher --------------------------------------------------------------


def launch_gui():
    """Launch the Qt GUI front-end (:mod:`greencrypt.gui`).

    The import is done lazily so that CLI users never need PySide6 installed:
    the ``greencrypt`` package imports fine with only pycryptodomex present.
    """
    try:
        from .gui import main as gui_main
    except ImportError as e:
        print(f"[!] Could not start the GUI: {e}")
        print("    Install PySide6 and compile the UI:")
        print("      pip install pyside6")
        print("      pyside6-uic greencrypt/gui/main.ui -o greencrypt/gui/main_ui.py")
        print("    Or run with -i for the interactive CLI.")
        sys.exit(1)

    gui_main()  # builds QApplication and enters the Qt event loop


# -- Entry point ---------------------------------------------------------------


def main():
    # No arguments -> launch the graphical interface
    if len(sys.argv) == 1:
        launch_gui()
        return

    parser = build_parser()
    args = parser.parse_args()

    # Explicit interactive CLI menu (-i / --interactive)
    if args.interactive:
        interactive_mode()
        return

    # Pure command-line mode (-e / -d ...)
    cli_mode(args)


if __name__ == "__main__":
    main()
