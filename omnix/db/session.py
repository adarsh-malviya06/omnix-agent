"""
Database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from omnix.core.config import get_settings
from omnix.db.base import Base

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables."""
    import omnix.db.models  # ensure models are imported
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for obtaining transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
