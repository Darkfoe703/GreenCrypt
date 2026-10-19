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

.PHONY: help ui check-ui test run lint format build clean

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

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf build dist ./*.egg-info
	rm -f greencrypt/gui/main_ui.py.check
