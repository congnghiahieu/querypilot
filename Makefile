# This will pull variables from a .env file into the Makefile — but env vars passed from the shell still override those.
include .env
export

STREAMLIT_SERVER_ADDRESS ?= 0.0.0.0
STREAMLIT_SERVER_PORT ?= 8080

STREAMLIT_RUN = @streamlit run app.py --server.port $(STREAMLIT_SERVER_PORT) --server.address $(STREAMLIT_SERVER_ADDRESS)

env:
	@echo "ADDRESS: $(STREAMLIT_SERVER_ADDRESS), PORT: $(STREAMLIT_SERVER_PORT)"

run:
	$(STREAMLIT_RUN)

dev:
	$(STREAMLIT_RUN) --server.runOnSave true

lint:
	@ruff check . --fix

format: lint
	@ruff format .

freeze:
	@uv export --format requirements-txt --no-dev > requirements.lock
	@uv export --format requirements-txt --dev > requirements.dev.lock
