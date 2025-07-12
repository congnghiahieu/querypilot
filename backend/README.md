- Cài đặt hoàn thiện phần RAG cho tính năng upload knowledge base và trả lời câu hỏi dựa trên knowledge_base từ vector store:
1. Khi người dùng upload knowledge base, bao gồm 3 định dạng PDF, CSV, EXCEL, hoặc là 1 đoạn text thì tôi muốn cài đặt RAG để xử lý 4 loại dữ liệu này. Với 3 loại file thì chunking để implement RAG
3. Ngoài chunking thì tôi muốn từ dữ liệu của file hoặc dữ liệu text đã được chunking, tôi muốn call đến LLM để biết được insight hữu ích suy luận được từ tài liệu là gì
4. Để gọi đến LLM hãy xem file settings.py, tôi là LLM_CLIENT, LLM_* để bạn sử dụng. Chú ý tôi sử dụng Deepseek LLM
5. Sau khi tiền xử lý tài liệu thì tôi muốn lưu vào database 2 thông tin, 1 là thông tin về knowledge base (file hoặc text), 2 là insight của tài liệu đó. Hãy sử dụng file knowledge_base.py gồm 2 class KnowledgeBase và KnowledgeBaseInsight
6. Tôi đã có cài đặt phần RAG trong file rag.py
7. Hàm `process_document_insights` trong `kb.py` thãy thay thế bằng logic rag thật
7. Phần chức năng trả lời câu hỏi dựa trên RAG, hiện tại hàm `process_nl2sql_message` đang để placehodler. Hãy cài đặt thêm cho hàm này tính năng RAG với vector store từ knowledge base để thêm context. Còn phần giải pháp nl2sql thực sự thì vẫn để nguyên tôi sẽ cài đặt sau

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

ENV=dev # dev | prod
DEEPSEEK_API_KEY=<real_api_key>
SECRET_KEY=<real_secret_string>
CLIENT_URL=http://localhost:3000 # Frontend address for CORS settings
DATABASE_URL=postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot # Recommend run postgreSQL locally using `docker-compose.yml`, run before backend
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
