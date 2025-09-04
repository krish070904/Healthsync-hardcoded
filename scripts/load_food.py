# run this if you prefer CLI to load CSV into DB
import pandas as pd
from sqlalchemy import create_engine
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://hs_user:password@localhost:5432/healthsync_db")
engine = create_engine(DB_URL)
df = pd.read_csv("data/food_sample.csv")
df.to_sql("food_items", engine, if_exists="replace", index=False)
print("loaded", len(df))
