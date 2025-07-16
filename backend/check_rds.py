from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, create_engine, text

from src.core.settings import APP_SETTINGS

# ✅ 2. Tạo engine
engine = create_engine(
    APP_SETTINGS.get_database_url, echo=True, connect_args={"sslmode": "require"}
)

# ✅ 3. Dùng session kiểm tra kết nối
try:
    with Session(engine) as session:
        result = session.exec(text("SELECT 1;"))
        print("RDS OK:", result.one())
except SQLAlchemyError as e:
    print("RDS ERROR:", str(e))
