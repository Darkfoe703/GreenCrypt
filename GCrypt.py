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

File format (.aes):
  [16 bytes] magic header  -- b"GreenCrypt\xa8\xb7:\xf5\x83\xd7"
  [16 bytes] salt          -- random per-file (PBKDF2 input)
  [16 bytes] AES-EAX nonce
  [16 bytes] authentication tag
  [n  bytes] ciphertext
"""

import os
import sys
import argparse
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2
from Cryptodome.Hash import SHA256


# -- Constants -----------------------------------------------------------------

HEADER          = b"GreenCrypt\xa8\xb7:\xf5\x83\xd7"  # 16-byte magic / integrity marker
EXT             = ".aes"
SALT_LEN        = 16    # bytes of random salt stored in the blob
PBKDF2_ITER     = 200_000  # PBKDF2-SHA256 iteration count


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

def read_bytes(path: str) -> bytes:
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError as e:
        print(f"[!] Cannot read '{path}': {e}")
        sys.exit(1)


def write_bytes(path: str, data: bytes):
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError as e:
        print(f"[!] Cannot write '{path}': {e}")
        sys.exit(1)


def scan_dir(directory: str) -> list:
    """Return all file paths inside a directory (recursive)."""
    files = []
    for dirpath, _, filenames in os.walk(directory):
        for fname in filenames:
            files.append(os.path.join(dirpath, fname))
    return files


# -- Crypto core ---------------------------------------------------------------

def encrypt_bytes(password: str, plaintext: bytes) -> bytes:
    """
    Encrypt plaintext with AES-256-EAX.
    Generates a fresh random salt per call, derives the key with
    PBKDF2-SHA256 (200 000 iters), and returns a self-contained blob:

      HEADER(16) | SALT(16) | NONCE(16) | TAG(16) | CIPHERTEXT
    """
    salt   = get_random_bytes(SALT_LEN)
    key    = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return HEADER + salt + cipher.nonce + tag + ciphertext


def decrypt_bytes(password: str, blob: bytes) -> bytes:
    """
    Decrypt a GreenCrypt blob.
    Extracts the per-file salt from blob[16:32], re-derives the key,
    then verifies the tag and decrypts.
    Raises ValueError on bad header or authentication failure.
    """
    if not blob.startswith(HEADER):
        raise ValueError("Not a GreenCrypt file (invalid header).")
    salt       = blob[16:32]
    nonce      = blob[32:48]
    tag        = blob[48:64]
    ciphertext = blob[64:]
    key    = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


# -- High-level file operations ------------------------------------------------

def encrypt_file(password: str, path: str, delete_original: bool = False) -> str:
    """Encrypt a single file -> writes <path>.aes next to original."""
    plaintext = read_bytes(path)
    blob      = encrypt_bytes(password, plaintext)
    out_path  = path + EXT
    write_bytes(out_path, blob)
    print(f"  [+] Encrypted  -> {out_path}")
    if delete_original:
        os.remove(path)
        print(f"  [-] Deleted    -> {path}")
    return out_path


def decrypt_file(password: str, path: str, delete_original: bool = False) -> str:
    """Decrypt a single .aes file -> restores original filename."""
    blob = read_bytes(path)
    try:
        plaintext = decrypt_bytes(password, blob)
    except ValueError as e:
        print(f"  [!] {path}: {e}")
        sys.exit(1)

    # Recover original filename by stripping .aes extension
    out_path = path[: -len(EXT)] if path.endswith(EXT) else path + ".dec"

    # Write as text if valid UTF-8, otherwise as binary
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(plaintext.decode("utf-8"))
    except UnicodeDecodeError:
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
            encrypt_file(password, f, delete_original)
    else:
        print(f"[!] Target '{target}' not found.")
        sys.exit(1)


def decrypt_target(password: str, target: str, delete_original: bool = False):
    """Decrypt a .aes file or every .aes file inside a folder (recursive)."""
    if os.path.isfile(target):
        decrypt_file(password, target, delete_original)
    elif os.path.isdir(target):
        files = [f for f in scan_dir(target) if f.endswith(EXT)]
        if not files:
            print(f"[!] No {EXT} files found in '{target}'.")
            sys.exit(1)
        print(f"[*] Decrypting {len(files)} {EXT} file(s) in '{target}' ...")
        for f in files:
            decrypt_file(password, f, delete_original)
    else:
        print(f"[!] Target '{target}' not found.")
        sys.exit(1)


# -- Interactive mode ----------------------------------------------------------

def interactive_mode():
    banner()
    print("  1) Encrypt\n  2) Decrypt\n  3) Exit")
    choice = input("Select [1/2/3]: ").strip()
    if choice == "3":
        sys.exit(0)
    if choice not in ("1", "2"):
        print("[!] Invalid choice.")
        sys.exit(1)

    raw_target = input("File or folder path: ").strip()
    target = os.path.abspath(raw_target)
    if not os.path.exists(target):
        print(f"[!] '{target}' does not exist.")
        sys.exit(1)

    password = input("Password: ")

    answer = input("Delete original after processing? [y/N]: ").strip().lower()
    delete = answer == "y"

    print()
    if choice == "1":
        encrypt_target(password, target, delete_original=delete)
    else:
        decrypt_target(password, target, delete_original=delete)


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
    elif args.file:
        password = password_from_file(args.file)
    else:
        password = input("Password: ")

    print()
    if args.encrypt:
        encrypt_target(password, target, delete_original=args.delete)
    else:
        decrypt_target(password, target, delete_original=args.delete)


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
