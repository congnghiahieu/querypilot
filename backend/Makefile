SHELL := /bin/bash

# Variables definitions
# -----------------------------------------------------------------------------

ifeq ($(TIMEOUT),)
TIMEOUT := 60
endif

# Target section and Global definitions
# -----------------------------------------------------------------------------
.PHONY: clean

clean:
	@find . -name '*.pyc' -exec rm -rf {} \;
	@find . -name '__pycache__' -exec rm -rf {} \;
	@find . -name 'Thumbs.db' -exec rm -rf {} \;
	@find . -name '*~' -exec rm -rf {} \;
	rm -rf .cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf htmlcov
	rm -rf .tox/
	rm -rf docs/_build

generate_dot_env:
	@if [[ ! -e .env ]]; then \
		cp .env.example .env; \
	fi

venv:
	@uv venv .venv

install: generate_dot_env
	@uv sync

test: install
	@uv run pytest tests -vvv --show-capture=all

format:
	@uv run ruff check --fix .
	@uv run ruff format --check .

freeze:
	@uv export --format requirements-txt --no-annotate --no-header --no-hashes --no-dev --output-file requirements.txt
	@uv export --format requirements-txt --no-annotate --no-header --no-hashes --output-file requirements.dev.txt

dev:
	@uv run uvicorn main:app --reload --host 0.0.0.0 --port 8080

run:
	@uv run uvicorn main:app --host 0.0.0.0 --port 8080

up:
	@docker-compose build
	@docker-compose up -d

down:
	@docker-compose down
