import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# Read from env so it works locally, in Docker, and in CI
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nikhilsingh:new_password@localhost:5432/transcript_ai_insights",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
