# GreenCrypt

> AES-256-EAX file & folder encryption — scriptable CLI, interactive menu and Qt desktop GUI.

GreenCrypt is a small, dependency-light tool that encrypts individual files or whole
folders with **AES-256 in EAX mode** (authenticated encryption). It ships with three
front-ends that share the same hardened core:

| Front-end | How to start | Best for |
|-----------|--------------|----------|
| **Qt GUI** | `python -m greencrypt` (no arguments) | Dragging files, everyday use |
| **Interactive menu** | `python -m greencrypt -i` | Quick manual sessions in a terminal |
| **Command line** | `python -m greencrypt -e/-d ...` | Scripts, automation, SSH |

`GCrypt.py` is kept as a thin compatibility launcher, so the historical
`python GCrypt.py ...` invocations keep working unchanged. After installing the
package you also get the **`greencrypt`** and **`greencrypt-gui`** console scripts.

> **Note:** this is an educational / personal project. Please read the
> [Security notes](#security-notes) before trusting it with irreplaceable data.

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [File format](#file-format)
- [Project structure](#project-structure)
- [Testing](#testing)
- [GUI notes](#gui-notes)
- [Security notes](#security-notes)
- [License](#license)

## Features

- **AES-256-EAX** — authenticated encryption (confidentiality **and** integrity).
- **PBKDF2-HMAC-SHA256** key derivation, **200 000 iterations**, with a **random
  16-byte salt per file**.
- **Authenticated filename** — the original file name travels in the AEAD
  *Associated Data* (AAD), so tampering or renaming is detected.
- **Versioned binary header (v1)** for forward compatibility.
- **Binary-safe** — works with any file (images, archives, executables …).
- **Recursive** folder processing (encrypt every file / decrypt every `.aes`).
- **Never overwrites** an existing file — a numeric suffix (`name_1.ext`) is added.
- **Password handling without exposure** — read from a file or prompt; the CLI warns
  when the password is passed inline.
- Three interfaces: GUI, interactive menu and non-interactive CLI.

## Requirements

| Component | Version (tested) | Required for |
|-----------|------------------|--------------|
| Python | 3.13 (needs 3.10+) | Everything |
| [`pycryptodomex`](https://pypi.org/project/pycryptodomex/) | 3.24.1 | Crypto core |
| [`PySide6`](https://pypi.org/project/PySide6/) | 6.12.0 | GUI only (optional) |

> **Do not install `pycryptodome` and `pycryptodomex` together.** Both provide the
> same `Cryptodome` package namespace and will conflict. GreenCrypt prefers
> **`pycryptodomex`**.
>
> The core imports its crypto backend through a small shim, so it also runs against
> Debian's `python3-pycryptodome` (which ships the `Cryptodome` namespace) or the
> PyPI `pycryptodome` (whose namespace is `Crypto`) without any code change.

## Installation

### Run from the source tree

```bash
# 1. Clone
git clone git@github.com:Darkfoe703/GreenCrypt.git
cd GreenCrypt

# 2. Create and activate a virtual environment
python3 -m venv .
source bin/activate          # Linux / macOS
# bin\Scripts\activate       # Windows (cmd/powershell)

# 3. Install dependencies
pip install pycryptodomex            # crypto backend (required)
pip install PySide6                  # only if you want the graphical interface
```

(Alternatively, install the project itself with its extras — see
[Install as a package](#install-as-a-package) below.)

From the repository root you can then use `python -m greencrypt` (or the
`python GCrypt.py` shim) without installing anything else.

### Install as a package

The project ships a `pyproject.toml`, so it can be installed like any Python
package (this creates the `greencrypt` / `greencrypt-gui` commands):

```bash
pip install .              # CLI only
pip install '.[gui]'       # CLI + Qt GUI (pulls PySide6)
pip install -e .           # editable install for development
```

The generated Qt module (`main_ui.py`) is **committed on purpose**, so a GUI
install works out of the box — no compilation step required.

Verify the core imports:

```bash
python -c "from Cryptodome.Cipher import AES; from Cryptodome.Protocol.KDF import PBKDF2; print('OK')"
```

### Development setup

Dev tooling is declared as a [PEP 735](https://peps.python.org/pep-0735/)
dependency group, so it is **never installed for end users**:

```bash
pip install --group dev -e .   # project + dev tools (requires pip >= 25.1)
```

Common tasks are wrapped in the `Makefile` (it auto-detects the in-repo
virtualenv, so just run `make`):

```bash
make            # list all targets
make ui         # regenerate greencrypt/gui/main_ui.py from main.ui
make check-ui   # CI guard: fail if main_ui.py is stale (never commit drift)
make test       # run the test suite
make lint       # ruff check
make format     # ruff format
make build      # build sdist + wheel into dist/
```

> Runtime vs dev: `[project.optional-dependencies]` (`gui`) is a feature a *user*
> chooses; `[dependency-groups]` (`dev`) is tooling only *contributors* need.

## Usage

### 1. Graphical interface (no arguments)

```bash
python -m greencrypt
```

Drag files or folders onto the drop area (or use **Open**), type the password, and
press **Encrypt** / **Decrypt**. The window is a fixed 240×480 panel.

### 2. Interactive menu

```bash
python -m greencrypt -i
```

You get a small menu:

```
  1) Encrypt
  2) Decrypt
  3) Exit
```

### 3. Non-interactive command line

```bash
python -m greencrypt -e [options] TARGET   # encrypt
python -m greencrypt -d [options] TARGET   # decrypt
```

#### Options

| Option | Description |
|--------|-------------|
| `-e`, `--encrypt` | Encrypt the target file or folder |
| `-d`, `--decrypt` | Decrypt the target `.aes` file or folder |
| `-i`, `--interactive` | Run the interactive CLI menu (no GUI) |
| `-p`, `--password PASSWORD` | Password as a plain string ⚠ *(visible in `ps`/history)* |
| `-f`, `--file FILE` | Read the password from the first line of `FILE` |
| `--delete` | Delete the original file(s) after processing |
| `TARGET` | File or folder to process (positional, optional) |
| `-h`, `--help` | Show help and exit |

- `-e` / `-d` / `-i` are **mutually exclusive**.
- `-p` / `-f` are **mutually exclusive**; if neither is given, GreenCrypt prompts.

#### Examples

```bash
# Encrypt one file          -> secret.txt.aes
python -m greencrypt -e -p "my passphrase" secret.txt

# Decrypt it back           -> secret.txt (or secret_1.txt if it already exists)
python -m greencrypt -d -p "my passphrase" secret.txt.aes

# Encrypt a whole folder recursively, password read from a file
python -m greencrypt -e -f pass.txt ./documents

# Encrypt and then remove the original file
python -m greencrypt -e -p "my passphrase" --delete secret.txt

# Interactive menu / GUI
python -m greencrypt -i
python -m greencrypt
```

> After `pip install .` the same commands work without the `python -m` prefix,
> e.g. `greencrypt -e -p "my passphrase" secret.txt`.

## File format

The output is written next to the original with the `.aes` extension appended
(`photo.jpg` → `photo.jpg.aes`). A `.aes` file is a versioned binary blob:

| Offset | Size | Field | Notes |
|-------:|-----:|-------|-------|
| 0  | 8  | **Magic** | `b"GrCrypt\x01"` |
| 8  | 1  | **Version** | `0x01` |
| 9  | 1  | **Flags** | bit 0 = `filename_in_aad` |
| 10 | 6  | **Reserved** | zeroes |
| 16 | 16 | **Salt** | random per file (PBKDF2 input) |
| 32 | 16 | **Nonce** | AES-EAX nonce |
| 48 | 16 | **Tag** | EAX authentication tag |
| 64 | n  | **Ciphertext** | payload |

**Associated Data (authenticated, but not encrypted):**

```
[2 bytes] filename length (big-endian)  |  [n bytes] filename (UTF-8)
```

Notes:

- Decryption recovers the original name by stripping `.aes`; that name is fed back
  into the AAD. If the `.aes` file was **renamed**, verification fails
  (`MAC check failed`) — this is intentional and proves the ciphertext was not moved.
- Existing files are never overwritten: decryption falls back to `name_1.ext`.
- Older (pre-v1) files are rejected with *"Not a GreenCrypt file (invalid magic)"*.

## Project structure

```
GreenCrypt/
├── GCrypt.py                # compatibility launcher -> greencrypt.cli:main
├── pyproject.toml           # package metadata + console scripts + dependencies
├── Makefile                 # dev tasks (make ui, make test, make lint, ...)
├── greencrypt/              # the importable package
│   ├── __init__.py          # version + convenience re-exports
│   ├── __main__.py          # `python -m greencrypt`
│   ├── core.py              # crypto core: AES-256-EAX, .aes v1, PBKDF2 (UI-agnostic)
│   ├── cli.py               # banner + argparse + interactive menu + GUI launcher
│   └── gui/                 # Qt front-end (subpackage)
│       ├── __init__.py      # exposes main() lazily (no PySide6 on import)
│       ├── __main__.py      # `python -m greencrypt.gui`
│       ├── app.py           # MainWindow + QApplication bootstrap
│       ├── main.ui          # Qt Designer source — SINGLE SOURCE OF TRUTH
│       ├── main_ui.py       # generated by pyside6-uic — committed (see GUI notes)
│       └── assets/          # logo.jpg (drop area) + icon.png/icon.ico (window icon)
├── tools/
│   └── compile_ui.py        # regenerate / verify main_ui.py from main.ui
├── test_greencrypt.py       # self-contained test suite (30 tests)
├── LICENSE.md               # full GPLv3 text
└── pruebas/                 # legacy experiments — git-ignored, not part of the tool
```

### How the pieces fit together

```text
greencrypt.cli  ─┐
                 ├─►  greencrypt.core   (AES-256-EAX + .aes v1 + PBKDF2)
greencrypt.gui  ─┘
```

Both front-ends import the **same** core, so the file format and the crypto can
never drift apart between the CLI and the GUI.

## Testing

The suite is standalone (no `pytest` required) and uses temporary directories, so it
does not touch your files:

```bash
python test_greencrypt.py
# ...
#   Results: 30/30 passed ✓
```

It covers key derivation, AAD build/parse, header/version handling, file & folder
round-trips, binary integrity, `--delete`, unique output names and error paths.

## GUI notes

The interface is defined in Qt Designer XML: `greencrypt/gui/main.ui` is the
**single source of truth**. The Python module it compiles to
(`greencrypt/gui/main_ui.py`) is **generated** but **committed on purpose**, so a
fresh clone (and `pip install '.[gui]'`) works without running a compiler.

Regenerate it **only after editing `main.ui`**, never by hand:

```bash
make ui          # = python tools/compile_ui.py
make check-ui    # CI guard: exits non-zero if main_ui.py is stale
```

The `check-ui` target is designed for CI / pre-commit hooks, so a `main.ui`
change can never be committed without its regenerated `main_ui.py`.

Assets live in `greencrypt/gui/assets/`:

- **`logo.jpg`** — shown inside the drop area.
- **`icon.png`** — window / taskbar icon (also `icon.ico` for Windows packaging).

If an asset is absent, the GUI degrades gracefully (plain dark drop area, default icon).

## Security notes

- **Authenticated encryption (AEAD).** EAX is encrypt-then-MAC: any modification of the
  ciphertext, tag, salt, nonce or AAD is detected and rejected.
- **The filename is authenticated.** Renaming a `.aes` file breaks decryption by design.
- **No secrets in the header.** Magic, version, salt, nonce and tag are stored in clear;
  the salt is not sensitive, it only prevents precomputation across files.
- **Password strength matters.** PBKDF2 with 200 000 iterations slows brute force, but
  cannot rescue a weak passphrase. Use a long, unique one.
- **`-p` leaks.** A password passed on the command line is visible in the process list
  and shell history. Prefer `-f` or the interactive prompt.
- **`--delete` is not a secure erase.** It performs a normal unlink; the data may still
  be recoverable from the disk. Combine with full-disk encryption if that matters.
- **Symmetric only.** The same passphrase encrypts and decrypts everything — there is no
  key management, revocation or per-user access control.

## License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

```
GreenCrypt — AES-256-EAX file & folder encryption tool
Copyright (C) 2026  Marco Antonio Romero (@Darkfoe703)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

- SPDX identifier: `GPL-3.0-or-later`
- Full license text: [`LICENSE.md`](LICENSE.md) (also at <https://www.gnu.org/licenses/gpl-3.0.txt>)

### Contact

- **Email:** marcoromero.dev@gmail.com
- **Telegram:** [@Darkfoe703](https://t.me/Darkfoe703)
