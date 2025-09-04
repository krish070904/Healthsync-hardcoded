from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from datetime import datetime
from ..db import Base
import uuid

def new_id():
    return str(uuid.uuid4())

class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    symptom = Column(String, nullable=False)
    severity = Column(Integer)  # Scale of 1-10
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)