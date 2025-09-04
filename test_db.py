from sqlalchemy import create_engine

DATABASE_URL = "postgresql://hs_user:password@localhost:5432/healthsync_db"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("✅ Connection successful!")
except Exception as e:
    print("❌ Connection failed:", e)
