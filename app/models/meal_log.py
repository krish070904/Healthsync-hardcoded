from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from datetime import datetime
from ..db import Base
import uuid

def new_id():
    return str(uuid.uuid4())

class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    food_items = Column(Text)  # JSON string of food items
    calories = Column(Float)
    protein_grams = Column(Float)
    carbs_grams = Column(Float)
    fat_grams = Column(Float)
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)