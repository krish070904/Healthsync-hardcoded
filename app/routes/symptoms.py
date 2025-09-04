from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, auth
from ..db import get_db
from typing import List
from ..models import User

router = APIRouter(prefix="/symptoms", tags=["symptoms"])

@router.post("/log", response_model=schemas.SymptomLogResponse)
def log_symptoms(symptom_log: schemas.SymptomLogCreate, db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_active_user)):
    """Log symptoms and get AI classification"""
    # Validate user exists
    user = crud.get_user(db, symptom_log.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate severity scale
    if not 1 <= symptom_log.severity <= 10:
        raise HTTPException(status_code=400, detail="Severity must be between 1-10")
    
    # Create symptom log with AI classification
    db_result = crud.create_symptom_log(db, symptom_log)
    
    # Manually create a response that matches the expected schema
    result = schemas.SymptomLogResponse(
        id=db_result.id,
        user_id=db_result.user_id,
        symptoms=symptom_log.symptoms,  # Use the original symptoms list
        symptom=db_result.symptom,
        severity=db_result.severity,
        timestamp=db_result.timestamp,
        ai_classification=getattr(db_result, 'ai_classification', 'unknown'),
        needs_medical_attention=getattr(db_result, 'needs_medical_attention', False)
    )
    
    # Create health alert if medical attention is needed
    if result.needs_medical_attention:
        alert_message = f"Severe symptoms detected: {', '.join(result.symptoms)}. Please consult a healthcare provider."
        crud.create_health_alert(
            db, 
            symptom_log.user_id, 
            "severe_symptoms", 
            alert_message, 
            "high"
        )
    
    return result

@router.get("/user/{user_id}", response_model=List[schemas.SymptomLogResponse])
def get_user_symptoms(user_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get user's symptom history"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_logs = crud.get_user_symptoms(db, user_id, days)
    
    # Manually format each log to match the expected schema
    result = []
    for log in db_logs:
        symptoms = log.symptom.split(',') if log.symptom else []
        result.append(schemas.SymptomLogResponse(
            id=log.id,
            user_id=log.user_id,
            symptoms=symptoms,
            symptom=log.symptom,
            severity=log.severity,
            timestamp=log.timestamp,
            ai_classification=getattr(log, 'ai_classification', 'unknown'),
            needs_medical_attention=getattr(log, 'needs_medical_attention', False)
        ))
    
    return result

@router.get("/user/{user_id}/analysis")
def analyze_symptoms(user_id: str, db: Session = Depends(get_db)):
    """Get AI analysis of user's recent symptoms"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    symptoms = crud.get_user_symptoms(db, user_id, days=7)
    
    if not symptoms:
        return {"message": "No recent symptoms to analyze"}
    
    # Analyze patterns
    total_symptoms = len(symptoms)
    severe_symptoms = [s for s in symptoms if s.severity >= 7]
    flu_like_count = len([s for s in symptoms if s.ai_classification == "flu-like"])
    food_intolerance_count = len([s for s in symptoms if s.ai_classification == "food-intolerance"])
    
    # Most common symptoms
    all_symptoms = []
    for s in symptoms:
        all_symptoms.extend(s.symptoms)
    
    from collections import Counter
    symptom_counts = Counter(all_symptoms)
    most_common = symptom_counts.most_common(3)
    
    analysis = {
        "total_symptoms_logged": total_symptoms,
        "severe_symptoms_count": len(severe_symptoms),
        "ai_classifications": {
            "flu_like": flu_like_count,
            "food_intolerance": food_intolerance_count,
            "none": total_symptoms - flu_like_count - food_intolerance_count
        },
        "most_common_symptoms": most_common,
        "recommendations": []
    }
    
    # Generate recommendations based on patterns
    if flu_like_count > food_intolerance_count and flu_like_count > 2:
        analysis["recommendations"].append("Consider consulting a doctor for flu-like symptoms")
    
    if food_intolerance_count > 3:
        analysis["recommendations"].append("Consider keeping a food diary to identify trigger foods")
    
    if len(severe_symptoms) > 0:
        analysis["recommendations"].append("Seek medical attention for severe symptoms")
    
    return analysis
