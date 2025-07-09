FROM python:3.10.18-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt app/
RUN pip install --no-cache-dir -r app/requirements.txt

COPY main.py /app/main.py
COPY src/ /app/src/
COPY ./alembic /app/alembic/
COPY alembic.ini /app/alembic.ini

EXPOSE 8080

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port","8080"]