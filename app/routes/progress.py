from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from .. import schemas, crud, models
from ..db import get_db
from ..services.progress_tracker import ProgressTracker

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={404: {"description": "Not found"}},
)

@router.post("/log", response_model=schemas.ProgressCreate)
def log_progress(progress: schemas.ProgressCreate, db: Session = Depends(get_db)):
    """Log a new progress entry for a user"""
    # Validate user exists
    user = crud.get_user(db, progress.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create progress tracker service
    tracker = ProgressTracker(db)
    
    # Log the progress
    return tracker.log_progress(progress)

@router.get("/user/{user_id}", response_model=List[dict])
def get_user_progress(user_id: str, days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Get a user's progress history"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create progress tracker service
    tracker = ProgressTracker(db)
    
    # Get progress history
    progress_history = tracker.get_progress_history(user_id, days)
    
    # Convert to dict for response
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "weight_kg": p.weight_kg,
            "blood_sugar": p.blood_sugar,
            "blood_pressure_systolic": p.blood_pressure_systolic,
            "blood_pressure_diastolic": p.blood_pressure_diastolic,
            "notes": p.notes,
            "timestamp": p.timestamp
        }
        for p in progress_history
    ]

@router.get("/user/{user_id}/weight-trend")
def analyze_weight_trend(user_id: str, days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Analyze weight trends for a user"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create progress tracker service
    tracker = ProgressTracker(db)
    
    # Analyze weight trend
    return tracker.analyze_weight_trend(user_id, days)

@router.get("/user/{user_id}/blood-pressure-trend")
def analyze_blood_pressure_trend(user_id: str, days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Analyze blood pressure trends for a user"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create progress tracker service
    tracker = ProgressTracker(db)
    
    # Analyze blood pressure trend
    return tracker.analyze_blood_pressure_trend(user_id, days)

@router.get("/user/{user_id}/goal-progress")
def track_goal_progress(
    user_id: str, 
    goal_type: str = Query(..., description="Type of goal to track (weight, blood_sugar, blood_pressure)"),
    target_value: float = Query(..., description="Target value for the goal"),
    db: Session = Depends(get_db)
):
    """Track progress toward a specific health goal"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate goal type
    valid_goal_types = ["weight", "blood_sugar", "blood_pressure"]
    if goal_type not in valid_goal_types:
        raise HTTPException(status_code=400, detail=f"Invalid goal type. Must be one of: {', '.join(valid_goal_types)}")
    
    # Create progress tracker service
    tracker = ProgressTracker(db)
    
    # Track goal progress
    return tracker.track_goal_progress(user_id, goal_type, target_value)

@router.get("/user/{user_id}/health-report")
def generate_health_report(user_id: str, db: Session = Depends(get_db)):
    """Generate a comprehensive health report for a user"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create progress tracker service
    tracker = ProgressTracker(db)
    
    # Generate health report
    return tracker.generate_health_report(user_id)