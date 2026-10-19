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
GreenCrypt — cryptography core (UI-agnostic).

This module holds the pure logic, with **no dependency on argparse or Qt**:

  * AES-256-EAX encryption / decryption of byte blobs,
  * the versioned ``.aes`` container format (v1),
  * PBKDF2-HMAC-SHA256 key derivation,
  * high-level file and folder helpers.

Both front-ends reuse it:

  * ``greencrypt.cli`` — command line + interactive menu,
  * ``greencrypt.gui`` — Qt desktop application.

File format (.aes) v1:
  [8 bytes]  magic       -- b"GrCrypt\\x01"
  [1 byte]   version     -- 0x01
  [1 byte]   flags       -- bit 0: filename_in_aad
  [6 bytes]  reserved    -- zeroes
  [16 bytes] salt        -- random per-file (PBKDF2 input)
  [16 bytes] AES-EAX nonce
  [16 bytes] authentication tag
  [n  bytes] ciphertext

Associated Data (AAD, authenticated but not encrypted):
  [2 bytes]  filename_len (big-endian)
  [n bytes]  filename (UTF-8)
"""

from __future__ import annotations

import os
import struct

# -- Crypto backend ------------------------------------------------------------
# Import from whichever namespace is available so the same source runs against:
#   * the PyPI package ``pycryptodomex``   -> ``Cryptodome`` (recommended)
#   * Debian's ``python3-pycryptodome``    -> ``Cryptodome`` (packaged as pycryptodomex)
#   * the PyPI package ``pycryptodome``    -> ``Crypto``
# Installing both ``pycryptodome`` and ``pycryptodomex`` together is still a bad
# idea (they share the top-level namespace); this shim just makes the import
# resilient to which one a given distribution ships.
try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Random import get_random_bytes
    from Cryptodome.Protocol.KDF import PBKDF2
    from Cryptodome.Hash import SHA256
except ImportError:  # pragma: no cover - depends on what is installed
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA256


# -- Constants -----------------------------------------------------------------

MAGIC             = b"GrCrypt\x01"   # 8 bytes
CURRENT_VERSION   = 1
FLAG_FILENAME_AAD = 0x01             # bit 0: filename included in AAD
HEADER_SIZE       = 16               # magic(8) + version(1) + flags(1) + reserved(6)
EXT               = ".aes"
SALT_LEN          = 16
PBKDF2_ITER       = 200_000


class GreenCryptError(Exception):
    """Base exception for all recoverable GreenCrypt errors.

    Kept in the core so that every front-end (CLI, GUI, third-party code) can
    catch a single, well-defined exception type instead of letting ``sys.exit``
    bubble up from library code.
    """


# -- Key derivation ------------------------------------------------------------

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES-256 key from a password + salt.

    Uses PBKDF2-HMAC-SHA256 with 200 000 iterations.
    """
    return PBKDF2(password, salt, dkLen=32, count=PBKDF2_ITER, hmac_hash_module=SHA256)


def password_from_file(path: str) -> str:
    """Read the password from the first line of a file (stripped).

    Raises :class:`GreenCryptError` (instead of exiting) so each front-end can
    report the problem its own way.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            pw = f.readline().strip()
    except OSError as e:
        raise GreenCryptError(f"Cannot read password file '{path}': {e}") from e
    if not pw:
        raise GreenCryptError(f"Password file '{path}' is empty.")
    return pw


# -- Low-level I/O -------------------------------------------------------------

def read_bytes(path: str) -> bytes:
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError as e:
        raise GreenCryptError(f"Cannot read '{path}': {e}") from e


def write_bytes(path: str, data: bytes):
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError as e:
        raise GreenCryptError(f"Cannot write '{path}': {e}") from e


def scan_dir(directory: str) -> list:
    """Return all file paths inside a directory (recursive)."""
    files = []
    for dirpath, _, filenames in os.walk(directory):
        for fname in filenames:
            files.append(os.path.join(dirpath, fname))
    return files


# -- Crypto core ---------------------------------------------------------------

def _build_aad(filename: str) -> bytes:
    """Build Associated Data: 2-byte length (big-endian) + UTF-8 filename."""
    name_bytes = filename.encode("utf-8")
    if len(name_bytes) > 65535:
        raise ValueError("Filename too long for AAD")
    return struct.pack(">H", len(name_bytes)) + name_bytes


def _parse_aad(aad: bytes) -> str:
    """Parse AAD and return filename."""
    if len(aad) < 2:
        raise ValueError("AAD too short")
    name_len = struct.unpack(">H", aad[:2])[0]
    if len(aad) != 2 + name_len:
        raise ValueError("AAD length mismatch")
    return aad[2:].decode("utf-8")


def encrypt_bytes(password: str, plaintext: bytes, filename: str) -> bytes:
    """Encrypt ``plaintext`` with AES-256-EAX and the filename in the AAD.

    Returns the versioned blob:

      MAGIC(8) | VER(1) | FLAGS(1) | RESERVED(6) | SALT(16) | NONCE(16) | TAG(16) | CIPHERTEXT
    """
    salt = get_random_bytes(SALT_LEN)
    key = derive_key(password, salt)

    aad = _build_aad(filename)
    cipher = AES.new(key, AES.MODE_EAX)
    cipher.update(aad)  # Include filename in authentication
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # Build versioned header
    header = MAGIC + bytes([CURRENT_VERSION, FLAG_FILENAME_AAD]) + b"\x00" * 6
    return header + salt + cipher.nonce + tag + ciphertext


def decrypt_bytes(password: str, blob: bytes, expected_filename: str | None = None) -> bytes:
    """Decrypt a GreenCrypt blob (v1).

    Verifies header, extracts salt, uses filename from AAD for authentication.
    Raises ``ValueError`` on bad header, version mismatch, or authentication failure.
    """
    if len(blob) < HEADER_SIZE + SALT_LEN + 16 + 16:  # header + salt + nonce + tag minimum
        raise ValueError("Blob too small to be a GreenCrypt file.")

    # Parse header
    magic = blob[:8]
    if magic != MAGIC:
        raise ValueError("Not a GreenCrypt file (invalid magic).")

    version = blob[8]
    if version != CURRENT_VERSION:
        raise ValueError(f"Unsupported GreenCrypt version: {version} (expected {CURRENT_VERSION})")

    flags = blob[9]
    use_filename_aad = bool(flags & FLAG_FILENAME_AAD)

    # Extract components
    salt = blob[16:32]
    nonce = blob[32:48]
    tag = blob[48:64]
    ciphertext = blob[64:]

    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    if use_filename_aad:
        if expected_filename is None:
            raise ValueError("Filename required for AAD verification but not provided.")
        aad = _build_aad(expected_filename)
        cipher.update(aad)

    return cipher.decrypt_and_verify(ciphertext, tag)


# -- High-level file operations ------------------------------------------------

def encrypt_file(password: str, path: str, delete_original: bool = False) -> str:
    """Encrypt a single file -> writes ``<path>.aes`` next to the original."""
    plaintext = read_bytes(path)
    filename = os.path.basename(path)
    blob = encrypt_bytes(password, plaintext, filename)
    out_path = path + EXT
    write_bytes(out_path, blob)
    print(f"  [+] Encrypted  -> {out_path}")
    if delete_original:
        os.remove(path)
        print(f"  [-] Deleted    -> {path}")
    return out_path


def _unique_output_path(directory: str, base_name: str) -> str:
    """Generate a non-existing output path, appending ``_N`` if needed."""
    out_path = os.path.join(directory, base_name)
    if not os.path.exists(out_path):
        return out_path
    name, ext = os.path.splitext(base_name)
    counter = 1
    while True:
        candidate = os.path.join(directory, f"{name}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def decrypt_file(password: str, path: str, delete_original: bool = False) -> str:
    """Decrypt a single ``.aes`` file -> restores the original filename from AAD."""
    blob = read_bytes(path)
    # We need the filename from the .aes file for AAD verification
    # The filename is the basename without .aes extension
    aes_filename = os.path.basename(path)
    if aes_filename.endswith(EXT):
        original_filename = aes_filename[:-len(EXT)]
    else:
        original_filename = aes_filename + ".dec"

    try:
        plaintext = decrypt_bytes(password, blob, expected_filename=original_filename)
    except ValueError as e:
        raise GreenCryptError(f"{path}: {e}") from e

    # Always write as binary; never attempt UTF-8 decoding
    directory = os.path.dirname(path)
    out_path = _unique_output_path(directory, original_filename)
    write_bytes(out_path, plaintext)

    print(f"  [+] Decrypted  -> {out_path}")
    if delete_original:
        os.remove(path)
        print(f"  [-] Deleted    -> {path}")
    return out_path


def encrypt_target(password: str, target: str, delete_original: bool = False):
    """Encrypt a file or every file inside a folder (recursive)."""
    if os.path.isfile(target):
        encrypt_file(password, target, delete_original)
    elif os.path.isdir(target):
        files = scan_dir(target)
        print(f"[*] Encrypting {len(files)} file(s) in '{target}' ...")
        for f in files:
            try:
                encrypt_file(password, f, delete_original)
            except GreenCryptError as e:
                print(f"  [!] {f}: {e}")
    else:
        raise GreenCryptError(f"Target '{target}' not found.")


def decrypt_target(password: str, target: str, delete_original: bool = False):
    """Decrypt a ``.aes`` file or every ``.aes`` file inside a folder (recursive)."""
    if os.path.isfile(target):
        decrypt_file(password, target, delete_original)
    elif os.path.isdir(target):
        files = [f for f in scan_dir(target) if f.endswith(EXT)]
        if not files:
            raise GreenCryptError(f"No {EXT} files found in '{target}'.")
        print(f"[*] Decrypting {len(files)} {EXT} file(s) in '{target}' ...")
        for f in files:
            try:
                decrypt_file(password, f, delete_original)
            except GreenCryptError as e:
                print(f"  [!] {f}: {e}")
    else:
        raise GreenCryptError(f"Target '{target}' not found.")
