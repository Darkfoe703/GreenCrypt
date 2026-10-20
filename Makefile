# GreenCrypt — developer tasks.
#
# Usage:
#   make              # show this help (same as `make help`)
#   make <target>
#
# Override the interpreter if needed, e.g.:
#   make test PYTHON=python3.13

# Prefer the in-repo virtualenv (./bin/python) when present; otherwise python3.
PYTHON ?= $(shell test -x ./bin/python && echo ./bin/python || command -v python3)

.PHONY: help ui check-ui test run lint format build standalone appimage appimage-docker clean

help:
	@echo "GreenCrypt — available targets:"
	@echo ""
	@echo "  make ui         Recompile greencrypt/gui/main_ui.py from main.ui"
	@echo "  make check-ui   Fail if main_ui.py is out of date with main.ui (CI)"
	@echo "  make test       Run the test suite"
	@echo "  make run        Launch the GUI (no args) via 'python -m greencrypt'"
	@echo "  make lint       Lint the code with ruff"
	@echo "  make format     Format the code with ruff"
	@echo "  make build      Build sdist + wheel into dist/"
	@echo "  make standalone Freeze the full app (CLI+GUI) with PyInstaller"
	@echo "  make appimage   Wrap the frozen bundle into a single-file AppImage"
	@echo "  make appimage-docker  Same AppImage, but built in a manylinux container"
	@echo "                  (portable glibc: runs on other distros). Needs Docker"
	@echo "  make clean      Remove caches and build artifacts"

# Regenerate the Qt UI module. Run this after editing main.ui.
ui:
	$(PYTHON) tools/compile_ui.py

# Anti-drift guard for CI / pre-commit: never commit a stale main_ui.py.
check-ui:
	$(PYTHON) tools/compile_ui.py --check

test:
	$(PYTHON) test_greencrypt.py

run:
	$(PYTHON) -m greencrypt

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

build:
	$(PYTHON) -m build

# Freeze the complete application (CLI + GUI) into dist/GreenCrypt/ (PyInstaller).
# Requires the "package" dependency group: pip install --group package -e .
standalone:
	$(PYTHON) -m PyInstaller greencrypt.spec --noconfirm

# Wrap the frozen bundle into a single-file AppImage (dist/GreenCrypt-<arch>.AppImage).
# Downloads appimagetool on first run; depends on `standalone` so it stays fresh.
appimage: standalone
	$(PYTHON) tools/build_appimage.py

# Portable AppImage: identical result to `appimage`, but frozen *inside* a
# manylinux_2_34 container (glibc 2.34) instead of the host's glibc, so it also
# runs on other/older distros. Requires Docker. The source tree is bind-mounted,
# so `make appimage-docker` picks up your local edits without rebuilding the
# image (the image only needs rebuilding when packaging/Dockerfile changes).
# Override the image name with `make appimage-docker IMAGE=foo`.
IMAGE ?= greencrypt-build
appimage-docker:
	docker build -f packaging/Dockerfile -t $(IMAGE) .
	docker run --rm \
	  --user "$$(id -u):$$(id -g)" \
	  -e HOME=/tmp -e PYTHONPATH=/src \
	  -v "$(CURDIR):/src" -w /src \
	  $(IMAGE) bash -c "/opt/gc-venv/bin/python -m PyInstaller greencrypt.spec --noconfirm && /opt/gc-venv/bin/python tools/build_appimage.py"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf build dist ./*.egg-info .ruff_cache .pytest_cache .mypy_cache
	rm -f greencrypt/gui/main_ui.py.check
