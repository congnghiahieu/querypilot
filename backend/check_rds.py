import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, create_engine, text

from src.core.settings import APP_SETTINGS


def create_db_if_not_exists():
    conn = psycopg2.connect(
        host=APP_SETTINGS.AWS_RDS_HOST,
        port=APP_SETTINGS.AWS_RDS_PORT,
        user=APP_SETTINGS.AWS_RDS_USERNAME,
        password=APP_SETTINGS.AWS_RDS_PASSWORD,
        dbname="postgres",  # Connect to default DB
        sslmode="require",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check existence
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", ("querypilot",))
    exists = cur.fetchone()

    if not exists:
        cur.execute('CREATE DATABASE "querypilot";')
        print("✅ Database 'querypilot' created.")
    else:
        print("ℹ️ Database 'querypilot' already exists.")

    cur.close()
    conn.close()


def get_engine():
    return create_engine(
        APP_SETTINGS.get_database_url,
        echo=True,
        connect_args={"sslmode": "require"},
    )


def check_rds_connection():
    engine = get_engine()
    print("▶️ Checking DB:", APP_SETTINGS.get_database_url)

    try:
        with Session(engine) as session:
            result = session.exec(text("SELECT 1;"))
            print("✅ RDS OK:", result.one())
    except SQLAlchemyError as e:
        print("❌ RDS ERROR:", str(e))


if __name__ == "__main__":
    create_db_if_not_exists()
    check_rds_connection()
