from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from src.core.settings import APP_SETTINGS

engine: Engine = create_engine(APP_SETTINGS.get_database_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
