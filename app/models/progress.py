from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from datetime import datetime
from ..db import Base
import uuid

def new_id():
    return str(uuid.uuid4())

class Progress(Base):
    __tablename__ = "progress"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False)
    weight_kg = Column(Float)
    blood_sugar = Column(Float)
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)