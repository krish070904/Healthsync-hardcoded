from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = "male"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None

class FoodItemIn(BaseModel):
    name: str
    serving_g: int
    calories_per_100g: float
    protein_g_per_100g: float
    fat_g_per_100g: float
    carbs_g_per_100g: float
    tags: Optional[str] = ""

class SymptomLogCreate(BaseModel):
    user_id: str
    symptoms: List[str]
    severity: int  # 1-10 scale

class SymptomLogResponse(BaseModel):
    id: str
    user_id: str
    symptoms: List[str]
    symptom: Optional[str] = None  # Added to match the model
    severity: int
    timestamp: datetime
    ai_classification: Optional[str] = None
    needs_medical_attention: bool = False

class MealLogCreate(BaseModel):
    user_id: str
    meal_type: str
    foods: List[dict]  # List of food items with quantities
    symptoms_after: Optional[List[str]] = []

class MealLogResponse(BaseModel):
    id: str
    user_id: str
    meal_type: str
    foods: List[dict]
    total_calories: float
    timestamp: datetime
    symptoms_after: List[str]

class ProgressCreate(BaseModel):
    user_id: str
    weight_kg: Optional[float] = None
    blood_sugar: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    notes: Optional[str] = None

class HealthAlertResponse(BaseModel):
    id: str
    user_id: str
    alert_type: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

class MealPlanResponse(BaseModel):
    user_id: str
    daily_calories_target: int
    meals: dict
    recommendations: List[str]

class MealRecommendationCreate(BaseModel):
    user_id: str
    daily_calories_target: int
    protein_target_g: Optional[int] = None
    carbs_target_g: Optional[int] = None
    fat_target_g: Optional[int] = None
    meal_plan: Dict[str, Any]
    total_calories: Optional[int] = None
    total_protein_g: Optional[float] = None
    total_carbs_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    algorithm_version: Optional[str] = "1.0"
    criteria_weights: Optional[Dict[str, float]] = None

class MealRecommendationUpdate(BaseModel):
    user_rating: Optional[int] = None
    user_followed: Optional[bool] = None
    user_feedback: Optional[str] = None
    symptoms_reported: Optional[List[str]] = None
    health_metrics_after: Optional[Dict[str, Any]] = None
    followed_at: Optional[datetime] = None

class MealRecommendationRequest(BaseModel):
    user_id: str
    goal: Optional[str] = "maintenance"
    macro_profile: Optional[str] = "balanced"
    avoid_ingredients: Optional[List[str]] = None

class MealRecommendationResponse(BaseModel):
    id: str
    user_id: str
    daily_calories_target: int
    protein_target_g: Optional[int]
    carbs_target_g: Optional[int]
    fat_target_g: Optional[int]
    meal_plan: Dict[str, Any]
    total_calories: Optional[int]
    total_protein_g: Optional[float]
    total_carbs_g: Optional[float]
    total_fat_g: Optional[float]
    user_rating: Optional[int]
    user_followed: Optional[bool]
    user_feedback: Optional[str]
    algorithm_version: str
    criteria_weights: Optional[Dict[str, float]]
    created_at: datetime
    followed_at: Optional[datetime]
    symptoms_reported: Optional[List[str]]
    health_metrics_before: Optional[Dict[str, Any]]
    health_metrics_after: Optional[Dict[str, Any]]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
