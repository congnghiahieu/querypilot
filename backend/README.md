# QueryPilot

## Dowload dataset

- Please download dataset at [here](https://drive.google.com/drive/folders/1ULVZNXlYoXFdZBoDg87rwTbGXiO11yFb?usp=sharing) and put it (BIRD_dataset) in the top-level of directory
- Download 3 files [1](https://drive.google.com/file/d/1UmYvqLLxEoRsYnkde3rsnzEwEQn6I4xz/view?usp=sharing), [2](https://drive.google.com/file/d/1hAE7vK485lRaGZ521gZUabe4sa8JmRJf/view?usp=sharing), [3](https://drive.google.com/file/d/1wYj-zm7izgjuyBwJr8o-N_dmmSepB99P/view?usp=sharing) and put it in this `backend` folder

## Requirements

- Python >= 3.10
- Backend project use Makefile so need `make`
- Backend use [uv](https://docs.astral.sh/uv/) package manager. Install via `pipx install uv` or `pip install uv`. Please use `uv` instead of `pip`

- Some `uv` usage example:

```bash
uv add numpy # add a new dependency, equals to `pip install`
uv add ruff --dev # add a new dev dependency, equals to `pip install`
uv venv # create new venv, equals to `python -m venv .venv`
uv sync # dowload all dependencies listed in pyproject.toml, equals to `pip install -r requirements`
```

## Set up environment

- Run `make generate_dot_env` if file `.env` doesn't exists, see below example


```bash
# .env

ENV=local # local | aws
STAGE=dev # dev | prod
DEEPSEEK_API_KEY=<real_api_key>
SECRET_KEY=<real_secret_string>
CLIENT_URL=http://localhost:3000 # Frontend address for CORS settings
DATABASE_URL=postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot # Recommend run postgreSQL locally using `docker-compose.yml`, run before backend

# AWS S3 Configuration (only required when ENV=aws)
AWS_ACCESS_KEY_ID=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=<your_s3_bucket_name>
AWS_S3_BUCKET_URL=<optional_custom_s3_url>
```

## Install dependencies

- Create virtual env, install dependencies and activate:

```bash
uv sync
source ./.venv/bin/activate
```

- Run backend:

```bash
make dev # for dev environment
make run # for prod environment
```
