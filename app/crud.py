from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta
import joblib
import numpy as np
from .models.meal_recommendation import MealRecommendation
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    user_data = user.dict()
    user_data.pop("password")
    user_data["hashed_password"] = hashed_password
    u = models.User(**user_data)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def bulk_insert_foods_from_df(db: Session, df):
    from .models import FoodItem
    for _, row in df.iterrows():
        f = FoodItem(
            name=row['name'],
            serving_g=int(row['serving_g']),
            calories_per_100g=float(row['calories_per_100g']),
            protein_g_per_100g=float(row['protein_g_per_100g']),
            fat_g_per_100g=float(row['fat_g_per_100g']),
            carbs_g_per_100g=float(row['carbs_g_per_100g']),
            tags=row.get('tags', "")
        )
        db.add(f)
    db.commit()

# Symptom logging functions
def create_symptom_log(db: Session, symptom_log: schemas.SymptomLogCreate):
    # Load AI model for symptom classification
    try:
        model = joblib.load("models/symptom_model.joblib")
        # Convert symptoms to feature vector (simplified)
        symptoms = symptom_log.symptoms
        features = [
            1 if 'fever' in [s.lower() for s in symptoms] else 0,
            1 if 'nausea' in [s.lower() for s in symptoms] else 0,
            1 if 'bloating' in [s.lower() for s in symptoms] else 0,
            1 if 'headache' in [s.lower() for s in symptoms] else 0
        ]
        classification = model.predict([features])[0]
        classification_map = {0: "none", 1: "flu-like", 2: "food-intolerance"}
        ai_classification = classification_map.get(classification, "unknown")
        
        # Determine if medical attention is needed
        needs_medical_attention = (
            symptom_log.severity >= 8 or 
            'fever' in [s.lower() for s in symptoms] or
            'severe' in [s.lower() for s in symptoms]
        )
    except:
        ai_classification = "unknown"
        needs_medical_attention = symptom_log.severity >= 8

    sl = models.SymptomLog(
        user_id=symptom_log.user_id,
        symptom=','.join(symptom_log.symptoms),  # Join the symptoms list into a comma-separated string
        severity=symptom_log.severity,
        notes=f"AI Classification: {ai_classification}"
    )
    # Add these as attributes after creation since they're not in the model
    sl.ai_classification = ai_classification
    sl.needs_medical_attention = needs_medical_attention
    db.add(sl)
    db.commit()
    db.refresh(sl)
    return sl

def get_user_symptoms(db: Session, user_id: str, days: int = 7):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    symptom_logs = db.query(models.SymptomLog).filter(
        models.SymptomLog.user_id == user_id,
        models.SymptomLog.timestamp >= cutoff_date
    ).order_by(models.SymptomLog.timestamp.desc()).all()
    
    # Convert symptom string to list for each log and add the required attributes
    for log in symptom_logs:
        # Extract AI classification from notes if available
        ai_class = "unknown"
        if log.notes and "AI Classification:" in log.notes:
            ai_class = log.notes.split("AI Classification:")[1].strip()
        
        # Add required attributes for the response schema
        if not hasattr(log, 'symptoms'):
            log.symptoms = log.symptom.split(',') if log.symptom else []
        if not hasattr(log, 'ai_classification'):
            log.ai_classification = ai_class
        if not hasattr(log, 'needs_medical_attention'):
            log.needs_medical_attention = log.severity >= 8
    
    return symptom_logs

# Meal logging functions
def create_meal_log(db: Session, meal_log: schemas.MealLogCreate):
    # Calculate total calories from foods
    total_calories = 0
    for food in meal_log.foods:
        # This is simplified - in real app you'd look up food in database
        if 'calories' in food:
            total_calories += food['calories']
    
    ml = models.MealLog(
        user_id=meal_log.user_id,
        meal_type=meal_log.meal_type,
        foods=meal_log.foods,
        total_calories=total_calories,
        symptoms_after=meal_log.symptoms_after or []
    )
    db.add(ml)
    db.commit()
    db.refresh(ml)
    return ml

def get_user_meals(db: Session, user_id: str, days: int = 7):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.MealLog).filter(
        models.MealLog.user_id == user_id,
        models.MealLog.timestamp >= cutoff_date
    ).order_by(models.MealLog.timestamp.desc()).all()

# Progress tracking functions
def create_progress(db: Session, progress: schemas.ProgressCreate):
    p = models.Progress(**progress.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def get_user_progress(db: Session, user_id: str, days: int = 30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.Progress).filter(
        models.Progress.user_id == user_id,
        models.Progress.timestamp >= cutoff_date
    ).order_by(models.Progress.timestamp.desc()).all()

# Health alert functions
def create_health_alert(db: Session, user_id: str, alert_type: str, message: str, severity: str = "medium"):
    alert = models.HealthAlert(
        user_id=user_id,
        alert_type=alert_type,
        message=message,
        severity=severity
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def get_user_alerts(db: Session, user_id: str, unread_only: bool = False):
    query = db.query(models.HealthAlert).filter(models.HealthAlert.user_id == user_id)
    if unread_only:
        query = query.filter(models.HealthAlert.is_read == False)
    return query.order_by(models.HealthAlert.created_at.desc()).all()

def mark_alert_read(db: Session, alert_id: str):
    alert = db.query(models.HealthAlert).filter(models.HealthAlert.id == alert_id).first()
    if alert:
        alert.is_read = True
        db.commit()
    return alert

# Meal recommendation functions
def create_meal_recommendation(db: Session, recommendation: schemas.MealRecommendationCreate):
    """Create a new meal recommendation record"""
    rec = MealRecommendation(**recommendation.dict())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def get_meal_recommendation(db: Session, recommendation_id: str):
    """Get a specific meal recommendation by ID"""
    return db.query(MealRecommendation).filter(MealRecommendation.id == recommendation_id).first()

def get_user_meal_recommendations(db: Session, user_id: str, limit: int = 10):
    """Get a user's meal recommendation history, ordered by most recent"""
    return db.query(MealRecommendation).filter(
        MealRecommendation.user_id == user_id
    ).order_by(MealRecommendation.created_at.desc()).limit(limit).all()

def update_meal_recommendation(db: Session, recommendation_id: str, update_data: schemas.MealRecommendationUpdate):
    """Update a meal recommendation with user feedback and follow-up data"""
    rec = db.query(MealRecommendation).filter(MealRecommendation.id == recommendation_id).first()
    if not rec:
        return None
        
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(rec, key, value)
        
    # If user_followed is being set to True, update the followed_at timestamp
    if update_dict.get('user_followed') is True and not rec.followed_at:
        rec.followed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(rec)
    return rec

def get_most_successful_recommendations(db: Session, user_id: str, limit: int = 5):
    """Get the most successful meal recommendations for a user based on rating"""
    return db.query(MealRecommendation).filter(
        MealRecommendation.user_id == user_id,
        MealRecommendation.user_rating != None,
        MealRecommendation.user_followed == True
    ).order_by(MealRecommendation.user_rating.desc()).limit(limit).all()
