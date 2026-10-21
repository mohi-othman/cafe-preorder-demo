from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(settings.database_url)


def create_schema() -> None:
    from app import models  # noqa: F401  (register tables)

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
