from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, create_engine, text

from src.core.settings import APP_SETTINGS


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
    check_rds_connection()
