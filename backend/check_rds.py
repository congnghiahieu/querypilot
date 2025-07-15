import psycopg2
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from src.core.settings import APP_SETTINGS

engine: Engine = create_engine(APP_SETTINGS.get_database_url, echo=True)
with Session(engine) as session:
    pass

conn = psycopg2.connect(
    host=APP_SETTINGS.AWS_RDS_HOST,
    port=APP_SETTINGS.AWS_RDS_PORT,
    dbname=APP_SETTINGS.AWS_RDS_DB_NAME,
    user=APP_SETTINGS.AWS_RDS_USERNAME,
    password=APP_SETTINGS.AWS_RDS_USERNAME,
    sslmode="require",
)
cur = conn.cursor()
cur.execute("SELECT 1;")
print("RDS OK:", cur.fetchone())
conn.close()
