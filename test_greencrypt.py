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
test_greencrypt.py — Test suite for GreenCrypt core (v1).
"""

import os
import sys
import struct
import tempfile

# Ensure the 'greencrypt' package is importable from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greencrypt.core import (
    MAGIC,
    CURRENT_VERSION,
    FLAG_FILENAME_AAD,
    EXT,
    GreenCryptError,
    _build_aad,
    _parse_aad,
    encrypt_bytes,
    decrypt_bytes,
    encrypt_file,
    decrypt_file,
    encrypt_target,
    decrypt_target,
    _unique_output_path,
)

# ── helpers ────────────────────────────────────────────────────────────────────

PASS = "vaallover1121941999"
PASS2 = "wrong_password_xyz"

passed = 0
failed = 0


def ok(name):
    global passed
    passed += 1
    print(f"  [PASS] {name}")


def fail(name, reason=""):
    global failed
    failed += 1
    print(f"  [FAIL] {name}" + (f": {reason}" if reason else ""))


def section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ── 1. _build_aad / _parse_aad ────────────────────────────────────────────────

section("1. AAD build / parse")

try:
    aad = _build_aad("secret.txt")
    name_len = struct.unpack(">H", aad[:2])[0]
    assert name_len == len(b"secret.txt"), f"len mismatch: {name_len}"
    assert aad[2:] == b"secret.txt"
    ok("_build_aad encodes length + filename correctly")
except Exception as e:
    fail("_build_aad", str(e))

try:
    aad = _build_aad("secret.txt")
    fname = _parse_aad(aad)
    assert fname == "secret.txt", f"got {fname!r}"
    ok("_parse_aad round-trips filename")
except Exception as e:
    fail("_parse_aad round-trip", str(e))

try:
    _parse_aad(b"\x00")  # too short
    fail("_parse_aad rejects too-short AAD")
except ValueError:
    ok("_parse_aad rejects too-short AAD")
except Exception as e:
    fail("_parse_aad rejects too-short AAD", str(e))

try:
    bad = struct.pack(">H", 5) + b"ab"  # len=5 but only 2 bytes of name
    _parse_aad(bad)
    fail("_parse_aad rejects length mismatch")
except ValueError:
    ok("_parse_aad rejects length mismatch")
except Exception as e:
    fail("_parse_aad rejects length mismatch", str(e))

try:
    aad = _build_aad("ñoño_utf8_€.txt")
    fname = _parse_aad(aad)
    assert fname == "ñoño_utf8_€.txt"
    ok("_build_aad/_parse_aad handles UTF-8 filenames")
except Exception as e:
    fail("AAD UTF-8 round-trip", str(e))


# ── 2. encrypt_bytes / decrypt_bytes (core) ───────────────────────────────────

section("2. Crypto core (encrypt_bytes / decrypt_bytes)")

plaintext = b"Datos secretos de prueba 1234 \xff\x00\xab"
fname = "test_file.bin"

try:
    blob = encrypt_bytes(PASS, plaintext, fname)
    ok("encrypt_bytes returns without error")
except Exception as e:
    fail("encrypt_bytes", str(e))
    blob = None

if blob:
    # Blob structure
    try:
        assert blob[:8] == MAGIC, f"magic mismatch: {blob[:8]!r}"
        ok("Blob: magic bytes correct (b'GrCrypt\\x01')")
    except AssertionError as e:
        fail("Blob magic", str(e))

    try:
        assert blob[8] == CURRENT_VERSION, f"version={blob[8]}"
        ok(f"Blob: version byte = {blob[8]}")
    except AssertionError as e:
        fail("Blob version", str(e))

    try:
        assert blob[9] == FLAG_FILENAME_AAD, f"flags={blob[9]}"
        ok(f"Blob: flags byte = 0x{blob[9]:02x} (FLAG_FILENAME_AAD)")
    except AssertionError as e:
        fail("Blob flags", str(e))

    try:
        reserved = blob[10:16]
        assert reserved == b"\x00" * 6, f"reserved={reserved!r}"
        ok("Blob: reserved bytes are zeroes")
    except AssertionError as e:
        fail("Blob reserved", str(e))

    try:
        salt = blob[16:32]
        nonce = blob[32:48]
        tag = blob[48:64]
        ct = blob[64:]
        assert len(salt) == 16, f"salt len={len(salt)}"
        assert len(nonce) == 16, f"nonce len={len(nonce)}"
        assert len(tag) == 16, f"tag len={len(tag)}"
        assert len(ct) == len(plaintext), f"ct len={len(ct)}"
        ok(f"Blob: salt(16) | nonce(16) | tag(16) | ct({len(ct)}) — offsets correct")
    except AssertionError as e:
        fail("Blob field offsets", str(e))

    # Correct decrypt
    try:
        recovered = decrypt_bytes(PASS, blob, expected_filename=fname)
        assert recovered == plaintext, "data mismatch"
        ok("decrypt_bytes recovers original plaintext")
    except Exception as e:
        fail("decrypt_bytes correct roundtrip", str(e))

    # Per-file random salt: two encryptions of same data → different blobs
    try:
        blob2 = encrypt_bytes(PASS, plaintext, fname)
        salt1 = blob[16:32]
        salt2 = blob2[16:32]
        assert salt1 != salt2, "salts should differ"
        ok("Per-file random salt: two encryptions produce different salts")
    except Exception as e:
        fail("Per-file random salt", str(e))

    # Wrong password
    try:
        decrypt_bytes(PASS2, blob, expected_filename=fname)
        fail("decrypt_bytes rejects wrong password")
    except (ValueError, KeyError):
        ok("decrypt_bytes raises ValueError on wrong password")
    except Exception as e:
        fail("decrypt_bytes wrong password exception type", str(e))

    # Tampered filename in AAD
    try:
        decrypt_bytes(PASS, blob, expected_filename="wrong_name.bin")
        fail("decrypt_bytes rejects tampered filename")
    except (ValueError, KeyError):
        ok("decrypt_bytes raises ValueError on tampered filename (AAD integrity)")
    except Exception as e:
        fail("decrypt_bytes tampered filename exception type", str(e))

    # Bad magic
    try:
        bad_blob = b"BADMAGIC" + blob[8:]
        decrypt_bytes(PASS, bad_blob, expected_filename=fname)
        fail("decrypt_bytes rejects invalid magic")
    except ValueError:
        ok("decrypt_bytes raises ValueError on invalid magic")
    except Exception as e:
        fail("decrypt_bytes invalid magic exception type", str(e))

    # Blob too small
    try:
        decrypt_bytes(PASS, MAGIC + b"\x01\x01" + b"\x00" * 6, expected_filename=fname)
        fail("decrypt_bytes rejects too-small blob")
    except ValueError:
        ok("decrypt_bytes raises ValueError on too-small blob")
    except Exception as e:
        fail("decrypt_bytes too-small blob exception type", str(e))

    # Missing expected_filename when flag is set
    try:
        decrypt_bytes(PASS, blob, expected_filename=None)
        fail("decrypt_bytes rejects None filename when FLAG_FILENAME_AAD is set")
    except ValueError:
        ok("decrypt_bytes raises ValueError when expected_filename=None and flag set")
    except Exception as e:
        fail("decrypt_bytes None filename exception type", str(e))


# ── 3. _unique_output_path ────────────────────────────────────────────────────

section("3. _unique_output_path")

with tempfile.TemporaryDirectory() as tmpdir:
    try:
        p = _unique_output_path(tmpdir, "out.txt")
        assert p == os.path.join(tmpdir, "out.txt")
        ok("_unique_output_path returns base path when no conflict")
    except Exception as e:
        fail("_unique_output_path no conflict", str(e))

    try:
        open(os.path.join(tmpdir, "out.txt"), "w").close()
        p = _unique_output_path(tmpdir, "out.txt")
        assert p == os.path.join(tmpdir, "out_1.txt"), f"got {p}"
        ok("_unique_output_path appends _1 on first conflict")
    except Exception as e:
        fail("_unique_output_path _1 suffix", str(e))

    try:
        open(os.path.join(tmpdir, "out_1.txt"), "w").close()
        p = _unique_output_path(tmpdir, "out.txt")
        assert p == os.path.join(tmpdir, "out_2.txt"), f"got {p}"
        ok("_unique_output_path increments to _2 on second conflict")
    except Exception as e:
        fail("_unique_output_path _2 suffix", str(e))


# ── 4. encrypt_file / decrypt_file ────────────────────────────────────────────

section("4. File-level encrypt / decrypt")

with tempfile.TemporaryDirectory() as tmpdir:
    # text file
    orig_path = os.path.join(tmpdir, "hello.txt")
    content = b"Hola GreenCrypt v1!\nLinea 2.\n"
    with open(orig_path, "wb") as f:
        f.write(content)

    try:
        aes_path = encrypt_file(PASS, orig_path)
        assert aes_path == orig_path + EXT
        assert os.path.exists(aes_path)
        ok(f"encrypt_file creates {os.path.basename(aes_path)}")
    except Exception as e:
        fail("encrypt_file", str(e))
        aes_path = None

    if aes_path:
        try:
            out = decrypt_file(PASS, aes_path)
            # _unique_output_path may add _1 suffix if orig_path already exists
            with open(out, "rb") as f:
                recovered = f.read()
            assert recovered == content, f"data mismatch: {recovered!r}"
            ok("decrypt_file restores original filename and content")
        except Exception as e:
            fail("decrypt_file", str(e))

        # Wrong password on file
        try:
            decrypt_file(PASS2, aes_path)
            fail("decrypt_file rejects wrong password")
        except GreenCryptError:
            ok("decrypt_file raises GreenCryptError on wrong password")
        except Exception as e:
            fail("decrypt_file wrong password exception type", str(e))

    # Binary file (no UTF-8)
    bin_path = os.path.join(tmpdir, "data.bin")
    bin_content = bytes(range(256)) * 4
    with open(bin_path, "wb") as f:
        f.write(bin_content)

    try:
        aes_bin = encrypt_file(PASS, bin_path)
        out_bin = decrypt_file(PASS, aes_bin)
        with open(out_bin, "rb") as f:
            recovered_bin = f.read()
        assert recovered_bin == bin_content, "binary content mismatch"
        ok("encrypt/decrypt_file handles pure binary content correctly")
    except Exception as e:
        fail("Binary file roundtrip", str(e))

    # --delete flag
    del_src = os.path.join(tmpdir, "ephemeral.txt")
    with open(del_src, "wb") as f:
        f.write(b"delete me")
    try:
        aes_del = encrypt_file(PASS, del_src, delete_original=True)
        assert not os.path.exists(del_src), "original should be deleted"
        ok("encrypt_file --delete removes original")
    except Exception as e:
        fail("encrypt_file --delete", str(e))


# ── 5. encrypt_target / decrypt_target ────────────────────────────────────────

section("5. Target-level encrypt / decrypt (folder)")

with tempfile.TemporaryDirectory() as tmpdir:
    # Create 3 files
    files_content = {
        "a.txt": b"File A content",
        "b.txt": b"File B content",
        "sub/c.txt": b"File C in subfolder",
    }
    for rel, data in files_content.items():
        full = os.path.join(tmpdir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)

    try:
        encrypt_target(PASS, tmpdir)
        aes_files = []
        for root, _, fnames in os.walk(tmpdir):
            aes_files += [os.path.join(root, fn) for fn in fnames if fn.endswith(EXT)]
        assert len(aes_files) == 3, f"expected 3 .aes, got {len(aes_files)}"
        ok(f"encrypt_target encrypted {len(aes_files)} files in folder (recursive)")
    except Exception as e:
        fail("encrypt_target folder", str(e))

    try:
        decrypt_target(PASS, tmpdir)
        for rel, data in files_content.items():
            full = os.path.join(tmpdir, rel)
            with open(full, "rb") as f:
                assert f.read() == data, f"content mismatch for {rel}"
        ok("decrypt_target restored all files with correct content")
    except Exception as e:
        fail("decrypt_target folder", str(e))

    # Non-existent target
    try:
        encrypt_target(PASS, "/tmp/__no_such_path_xyz__")
        fail("encrypt_target rejects non-existent target")
    except GreenCryptError:
        ok("encrypt_target raises GreenCryptError for non-existent target")
    except Exception as e:
        fail("encrypt_target non-existent target exception type", str(e))

    # decrypt_target on folder with no .aes files
    empty_dir = os.path.join(tmpdir, "empty_sub")
    os.makedirs(empty_dir, exist_ok=True)
    # remove any .aes from empty_dir scope
    try:
        decrypt_target(PASS, empty_dir)
        fail("decrypt_target raises on folder with no .aes files")
    except GreenCryptError:
        ok("decrypt_target raises GreenCryptError when no .aes files found")
    except Exception as e:
        fail("decrypt_target no .aes exception type", str(e))


# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'═' * 60}")
total = passed + failed
print(f"  Results: {passed}/{total} passed", "✓" if failed == 0 else f"— {failed} FAILED")
print(f"{'═' * 60}\n")
sys.exit(0 if failed == 0 else 1)
