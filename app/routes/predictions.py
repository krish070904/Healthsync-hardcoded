# app/routes/predictions.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from .. import crud, schemas
from ..db import get_db
from ..services.symptom_predictor import symptom_predictor

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.get("/symptoms/{user_id}/future")
def predict_future_symptoms(user_id: str, days_ahead: int = 3, db: Session = Depends(get_db)):
    """Predict future symptoms for a user based on their symptom history"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Load the model if not already loaded
    if not symptom_predictor.is_model_loaded and not symptom_predictor.load_model():
        raise HTTPException(
            status_code=503, 
            detail="Symptom prediction model not available. Please train the model first."
        )
    
    # Get predictions
    predictions = symptom_predictor.predict_future_symptoms(db, user_id, days_ahead)
    
    if "error" in predictions[0]:
        if "Not enough symptom history" in predictions[0]["error"]:
            raise HTTPException(
                status_code=400, 
                detail="Not enough symptom history for prediction. Please log more symptoms."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Prediction error: {predictions[0]['error']}"
            )
    
    return {
        "user_id": user_id,
        "days_predicted": days_ahead,
        "predictions": predictions
    }

@router.get("/symptoms/{user_id}/analysis")
def analyze_symptom_patterns(user_id: str, db: Session = Depends(get_db)):
    """Analyze symptom patterns for a user and provide insights"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get analysis
    analysis = symptom_predictor.analyze_symptom_patterns(db, user_id)
    
    if "message" in analysis:
        if "Not enough symptom history" in analysis["message"]:
            raise HTTPException(
                status_code=400, 
                detail="Not enough symptom history for analysis. Please log more symptoms."
            )
    
    return {
        "user_id": user_id,
        "analysis": analysis
    }

@router.post("/model/train")
def train_model(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Train the symptom prediction model (admin only)"""
    # This would typically have authentication/authorization
    # For now, we'll just check if we have enough data
    
    # Get all users with symptom logs
    users_with_symptoms = db.query(crud.models.SymptomLog.user_id).distinct().all()
    user_ids = [user[0] for user in users_with_symptoms]
    
    if not user_ids:
        raise HTTPException(
            status_code=400, 
            detail="No users with symptom data found. Cannot train model."
        )
    
    # Train in background to avoid blocking the API
    def train_model_task():
        symptom_predictor.train_model(db, user_ids)
    
    background_tasks.add_task(train_model_task)
    
    return {"message": "Model training started in the background"}

@router.get("/model/status")
def get_model_status():
    """Get the status of the symptom prediction model"""
    is_loaded = symptom_predictor.is_model_loaded or symptom_predictor.load_model()
    
    return {
        "model_loaded": is_loaded,
        "model_type": "GRU (Gated Recurrent Unit)",
        "features": symptom_predictor.SYMPTOM_FEATURES + ["severity"],
        "sequence_length": symptom_predictor.SEQUENCE_LENGTH,
        "can_predict": is_loaded
    }