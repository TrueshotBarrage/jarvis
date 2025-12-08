.PHONY: install dev lint format test test-cov run clean

# Python virtual environment
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Install production dependencies
install:
	$(PIP) install -r requirements.txt

# Install development dependencies
dev:
	$(PIP) install -r requirements-dev.txt

# Run linter
lint:
	$(VENV)/bin/ruff check .

# Auto-fix linting issues
fmt:
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

# Run tests
test:
	$(PYTHON) -m pytest

# Run tests with coverage
test-cov:
	$(PYTHON) -m pytest --cov=. --cov-report=term-missing --cov-report=html

# Run the server with auto-reload (loads .env if present)
run:
	@if [ -f .env ]; then export $$(grep -v '^#' .env | xargs) && $(PYTHON) -m uvicorn heart:app --reload; else $(PYTHON) -m uvicorn heart:app --reload; fi

# Clean up generated files
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache htmlcov .coverage
	rm -rf tests/__pycache__ apis/__pycache__
	rm -f speech.mp3
