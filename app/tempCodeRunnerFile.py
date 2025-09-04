import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# DATABASE_URL: use .env or fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hs_user:password@127.0.0.1:5432/healthsync_db")

# Force echo=True temporarily to see connection logs (can turn False later)
echo_mode = True

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=echo_mode
)

# Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection when running this file directly
if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful!")
    except Exception as e:
        print("❌ Database connection failed:", e)
