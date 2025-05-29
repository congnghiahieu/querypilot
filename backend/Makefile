# This will pull variables from a .env file into the Makefile — but env vars passed from the shell still override those.
include .env
export

QUERY_PILOT_PORT ?= 6060
QUERY_PILOT_HOST ?= 0.0.0.0
FASTAPI_RUN = @uvicorn main:app --host $(QUERY_PILOT_HOST) --port $(QUERY_PILOT_PORT)

env:
	@echo "HOST: $(QUERY_PILOT_HOST), PORT: $(QUERY_PILOT_PORT)"

run:
	$(FASTAPI_RUN)

dev:
	$(FASTAPI_RUN) --reload --reload-exclude '**/*.log'

lint:
	@ruff check . --fix

format: lint
	@ruff format .

PYTEST_COMMON_COMMAND = pytest tests/ --capture=tee-sys -vv --self-contained-html -n logical --diff-width=100

test-all:
	@$(PYTEST_COMMON_COMMAND) --html "./tests/reports/all.html"

freeze:
	@uv export --format requirements-txt --no-dev > requirements.lock
	@uv export --format requirements-txt --dev > requirements.dev.lock
	