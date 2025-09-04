from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, Boolean
from datetime import datetime
from .db import Base
import uuid

def new_id():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=new_id)
    name = Column(String)
    dob = Column(String)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    allergies = Column(JSON)
    diseases = Column(JSON)
    preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class MealRecommendation(Base):
    __tablename__ = "meal_recommendations"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False, index=True)
    daily_calories_target = Column(Integer, nullable=False)
    protein_target_g = Column(Integer)
    carbs_target_g = Column(Integer)
    fat_target_g = Column(Integer)
    meal_plan = Column(JSON, nullable=False)
    total_calories = Column(Integer)
    total_protein_g = Column(Float)
    total_carbs_g = Column(Float)
    total_fat_g = Column(Float)
    user_rating = Column(Integer)
    user_followed = Column(Boolean, default=None)
    user_feedback = Column(Text)
    algorithm_version = Column(String)
    criteria_weights = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    followed_at = Column(DateTime)
    symptoms_reported = Column(JSON)
    health_metrics_before = Column(JSON)
    health_metrics_after = Column(JSON)

class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(String, primary_key=True, default=new_id)
    name = Column(String, nullable=False)
    serving_g = Column(Integer)
    calories_per_100g = Column(Float)
    protein_g_per_100g = Column(Float)
    fat_g_per_100g = Column(Float)
    carbs_g_per_100g = Column(Float)
    tags = Column(Text)

class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False)
    symptoms = Column(JSON)  # List of symptoms
    severity = Column(Integer)  # 1-10 scale
    timestamp = Column(DateTime, default=datetime.utcnow)
    ai_classification = Column(String)  # flu-like, food-intolerance, none
    needs_medical_attention = Column(Boolean, default=False)

class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False)
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    foods = Column(JSON)  # List of food items consumed
    total_calories = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symptoms_after = Column(JSON)  # Any symptoms experienced after meal

class HealthAlert(Base):
    __tablename__ = "health_alerts"
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False)
    alert_type = Column(String)  # severe_symptoms, weight_change, etc.
    message = Column(Text)
    severity = Column(String)  # low, medium, high, critical
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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

