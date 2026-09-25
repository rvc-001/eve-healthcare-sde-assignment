from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings

# ---------------------------------------------------------------------------
# Engine — mirrors Forehand's db/client.ts (single DB client shared app-wide)
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.get_database_url,
    pool_pre_ping=True,  # keeps connections alive (equivalent to bun-sql's reconnect)
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base — all SQLAlchemy ORM models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Dependency — mirrors Forehand's .decorate("db", db) approach
# Used in FastAPI route dependencies: db: Session = Depends(get_db)
# ---------------------------------------------------------------------------
def get_db() -> Session:  # type: ignore[return]
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
