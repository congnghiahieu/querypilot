# QueryPilot

## Dataset Prepare

- Download dataset at https://bull-text-to-sql-benchmark.github.io/, put it under `dataset/` directory
- This repo use English dataset only
- Then the file structure should look like this:

```bash
. dataset/
├── BULL-en
├── database_en
```

## Requirements

- Python >= 3.10
- Backend project use Makefile so need `make`
- [Recommend] Backend use [uv](https://docs.astral.sh/uv/) package manager. Install via `pipx install uv` or `pip install uv`
- [Optional] Use `pip` to install dependencies instead of `uv`. Instruction below

## Set up environment

- Copy `.env` file from `.env.sample` and fill out at least required variable. For example:

```bash
LLM_API_KEY = "abcdefgh123456789"
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL_NAME = "deepseek-chat"
```

## Install dependencies

- Create virtual env, install dependencies and activate:

```bash
# if use uv
uv sync
source ./.venv/bin/activate

# if use pip
python3 -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.dev.lock # for dev environment
```

- Run backend:

```bash
make dev # for dev environment

make run # for prod environment
```

- Run test (no pytest):

```bash
cd tests/
python3 test_text2sql.py
```
