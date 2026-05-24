import os

from sqlmodel import Session, create_engine, SQLModel


def _build_database_url() -> str:
    # Prefer a full URL when provided (best for k8s secrets/configmaps).
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Fallback local defaults (SQLite) for development.
    db_path = os.getenv("DB_PATH", "./app.db")
    return f"sqlite:///{db_path}"


DATABASE_URL = _build_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
