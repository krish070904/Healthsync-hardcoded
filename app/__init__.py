from .db import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)