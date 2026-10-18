#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GreenCrypt — AES-256-EAX file/folder encryption tool.

CLI usage:
  python GCrypt.py -e -p "mypassword" secret.txt
  python GCrypt.py -d -p "mypassword" secret.txt.aes
  python GCrypt.py -e -f pass.txt folder/
  python GCrypt.py -e -p "mypassword" --delete secret.txt
  python GCrypt.py                         <- interactive menu

File format (.aes) v1:
  [8 bytes]  magic       -- b"GrCrypt\x01"
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

import os
import sys
import argparse
import struct
from pathlib import Path
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2
from Cryptodome.Hash import SHA256


# -- Constants -----------------------------------------------------------------

MAGIC           = b"GrCrypt\x01"   # 8 bytes
CURRENT_VERSION = 1
FLAG_FILENAME_AAD = 0x01           # bit 0: filename included in AAD
HEADER_SIZE     = 16               # magic(8) + version(1) + flags(1) + reserved(6)
EXT             = ".aes"
SALT_LEN        = 16
PBKDF2_ITER     = 200_000


# -- Banner --------------------------------------------------------------------

def banner():
    green = "\033[1;32m"
    reset = "\033[m"
    print(green + r"""
   ____                      ____                  _
  // ___|_ __ ___  ___ _ __  / ___|_ __ _   _ _ __ | |_
 | |  _| '__/ _ \/ _ | '_ \| |   | '__| | | | '_ \| __|
 | |_| | | |  __|  __| | | | |___| |  | |_| | |_) | |_
  \____|_|  \___|\___|_| |_|\____|_|   \__, | .__/ \__|
                                       |___/|_|
""" + reset)


# -- Key derivation ------------------------------------------------------------

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte AES-256 key from a password + salt.
    Uses PBKDF2-HMAC-SHA256 with 200 000 iterations.
    """
    return PBKDF2(password, salt, dkLen=32, count=PBKDF2_ITER, hmac_hash_module=SHA256)


def password_from_file(path: str) -> str:
    """Read the password from the first line of a file (stripped)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            pw = f.readline().strip()
        if not pw:
            print(f"[!] Password file '{path}' is empty.")
            sys.exit(1)
        return pw
    except OSError as e:
        print(f"[!] Cannot read password file '{path}': {e}")
        sys.exit(1)


# -- Low-level I/O -------------------------------------------------------------

class GreenCryptError(Exception):
    """Base exception for GreenCrypt errors."""
    pass


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
    """
    Encrypt plaintext with AES-256-EAX.
    Includes filename in AAD (authenticated but not encrypted).
    Returns versioned blob:

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
    """
    Decrypt a GreenCrypt blob (v1).
    Verifies header, extracts salt, uses filename from AAD for authentication.
    Raises ValueError on bad header, version mismatch, or authentication failure.
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
    """Encrypt a single file -> writes <path>.aes next to original."""
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
    """Generate a non-existing output path, appending _N if needed."""
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
    """Decrypt a single .aes file -> restores original filename from AAD."""
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
    """Decrypt a .aes file or every .aes file inside a folder (recursive)."""
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


# -- Interactive mode ----------------------------------------------------------

def interactive_mode():
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
            "  %(prog)s -e -p 'secret' photo.jpg\n"
            "  %(prog)s -d -p 'secret' photo.jpg.aes\n"
            "  %(prog)s -e -f pass.txt documents/\n"
            "  %(prog)s -e -p 'secret' --delete secret.txt\n"
            "  %(prog)s                      (interactive menu)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Action (mutually exclusive)
    action_grp = parser.add_mutually_exclusive_group()
    action_grp.add_argument(
        "-e", "--encrypt",
        action="store_true",
        help="Encrypt the target file or folder",
    )
    action_grp.add_argument(
        "-d", "--decrypt",
        action="store_true",
        help="Decrypt the target file or folder",
    )

    # Password source (mutually exclusive)
    pwd_grp = parser.add_mutually_exclusive_group()
    pwd_grp.add_argument(
        "-p", "--password",
        metavar="PASSWORD",
        help="Password as a plain string",
    )
    pwd_grp.add_argument(
        "-f", "--file",
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

    # Resolve password
    if args.password:
        password = args.password
        # Warn about password on CLI (visible in ps, history, logs)
        print("[!] WARNING: Password provided via -p/--password is visible in process list and shell history.")
        print("    Consider using -f/--file or interactive input instead.")
    elif args.file:
        password = password_from_file(args.file)
    else:
        password = input("Password: ")

    print()
    try:
        if args.encrypt:
            encrypt_target(password, target, delete_original=args.delete)
        else:
            decrypt_target(password, target, delete_original=args.delete)
    except GreenCryptError as e:
        print(f"[!] Error: {e}")
        sys.exit(1)


# -- Entry point ---------------------------------------------------------------

def main():
    # No arguments -> drop into interactive menu
    if len(sys.argv) == 1:
        interactive_mode()
        return

    parser = build_parser()
    args   = parser.parse_args()
    cli_mode(args)


if __name__ == "__main__":
    main()
