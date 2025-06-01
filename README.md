# QueryPilot

## Requirements

- Python >= 3.10
- Backend project use Makefile so need `make`
- [Recommend] Backend use [uv](https://docs.astral.sh/uv/) package manager. Install via `pipx install uv` or `pip install uv`
- [Optional] Use `pip` to install dependencies instead of `uv`. Instruction below

## Set up environment

- Copy `.env` file from `.env.sample` and fill out at least required variable

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
