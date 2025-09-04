from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..db import get_db
from typing import List

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/user/{user_id}", response_model=List[schemas.HealthAlertResponse])
def get_user_alerts(user_id: str, unread_only: bool = False, db: Session = Depends(get_db)):
    """Get user's health alerts"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud.get_user_alerts(db, user_id, unread_only)

@router.put("/{alert_id}/read")
def mark_alert_as_read(alert_id: str, db: Session = Depends(get_db)):
    """Mark a health alert as read"""
    alert = crud.mark_alert_read(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert marked as read", "alert_id": alert_id}

@router.get("/user/{user_id}/summary")
def get_alerts_summary(user_id: str, db: Session = Depends(get_db)):
    """Get summary of user's alerts"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    all_alerts = crud.get_user_alerts(db, user_id)
    unread_alerts = crud.get_user_alerts(db, user_id, unread_only=True)
    
    # Count alerts by severity
    severity_counts = {}
    alert_type_counts = {}
    
    for alert in all_alerts:
        severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        alert_type_counts[alert.alert_type] = alert_type_counts.get(alert.alert_type, 0) + 1
    
    # Get recent critical alerts
    critical_alerts = [alert for alert in all_alerts if alert.severity == "critical"][:5]
    
    summary = {
        "total_alerts": len(all_alerts),
        "unread_alerts": len(unread_alerts),
        "severity_distribution": severity_counts,
        "alert_type_distribution": alert_type_counts,
        "recent_critical_alerts": [
            {
                "id": alert.id,
                "message": alert.message,
                "created_at": alert.created_at
            }
            for alert in critical_alerts
        ]
    }
    
    return summary

@router.post("/user/{user_id}/check-health-status")
def check_health_status(user_id: str, db: Session = Depends(get_db)):
    """Check user's current health status and generate alerts if needed"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent symptoms and progress data
    recent_symptoms = crud.get_user_symptoms(db, user_id, days=3)
    recent_progress = crud.get_user_progress(db, user_id, days=7)
    
    alerts_generated = []
    
    # Check for severe symptoms
    severe_symptoms = [s for s in recent_symptoms if s.severity >= 8]
    if severe_symptoms:
        alert_message = f"Severe symptoms detected in the last 3 days. Please consult a healthcare provider."
        alert = crud.create_health_alert(db, user_id, "severe_symptoms", alert_message, "high")
        alerts_generated.append(alert)
    
    # Check for rapid weight changes
    if len(recent_progress) >= 2:
        weight_changes = []
        for i in range(1, len(recent_progress)):
            weight_diff = recent_progress[i-1].weight_kg - recent_progress[i].weight_kg
            weight_changes.append(abs(weight_diff))
        
        avg_weight_change = sum(weight_changes) / len(weight_changes)
        if avg_weight_change > 2:  # More than 2kg average change
            alert_message = f"Significant weight change detected ({avg_weight_change:.1f}kg average). Monitor your health."
            alert = crud.create_health_alert(db, user_id, "weight_change", alert_message, "medium")
            alerts_generated.append(alert)
    
    # Check for high blood pressure
    if recent_progress:
        latest = recent_progress[0]
        if latest.blood_pressure_systolic and latest.blood_pressure_systolic > 140:
            alert_message = f"High blood pressure detected ({latest.blood_pressure_systolic}/{latest.blood_pressure_diastolic}). Consider lifestyle changes."
            alert = crud.create_health_alert(db, user_id, "high_blood_pressure", alert_message, "medium")
            alerts_generated.append(alert)
    
    # Check for high blood sugar
    if recent_progress:
        latest = recent_progress[0]
        if latest.blood_sugar and latest.blood_sugar > 140:
            alert_message = f"High blood sugar detected ({latest.blood_sugar} mg/dL). Monitor your diet and consult a doctor."
            alert = crud.create_health_alert(db, user_id, "high_blood_sugar", alert_message, "medium")
            alerts_generated.append(alert)
    
    return {
        "health_status": "checked",
        "alerts_generated": len(alerts_generated),
        "new_alerts": [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity
            }
            for alert in alerts_generated
        ]
    }
