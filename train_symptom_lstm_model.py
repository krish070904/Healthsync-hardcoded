# train_symptom_lstm_model.py
import os
import sys
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base
from app.services.symptom_predictor import symptom_predictor
from app import crud, models

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def generate_synthetic_data(db: Session, num_users: int = 5, days_per_user: int = 30):
    """Generate synthetic symptom data for training the model"""
    print(f"Generating synthetic data for {num_users} users over {days_per_user} days each...")
    
    # Create synthetic users if needed
    users = db.query(models.User).limit(num_users).all()
    existing_users = len(users)
    
    if existing_users < num_users:
        print(f"Creating {num_users - existing_users} synthetic users...")
        for i in range(existing_users, num_users):
            user = models.User(
                name=f"Synthetic User {i+1}",
                gender="other",
                height_cm=170.0,
                weight_kg=70.0,
                allergies=[],
                diseases=[],
                preferences={}
            )
            db.add(user)
        db.commit()
        users = db.query(models.User).limit(num_users).all()
    
    # Generate symptom patterns for each user
    from datetime import datetime, timedelta
    import random
    
    symptom_types = [
        # Flu-like pattern
        {"symptoms": ["fever", "headache"], "classification": "flu-like", "severity": (6, 9)},
        # Food intolerance pattern
        {"symptoms": ["nausea", "bloating"], "classification": "food-intolerance", "severity": (4, 7)},
        # No symptoms pattern
        {"symptoms": [], "classification": "none", "severity": (1, 3)}
    ]
    
    # Create patterns with time dependencies
    for user in users:
        print(f"Generating data for user {user.id}...")
        
        # Create a pattern that changes over time
        # For example: none -> food-intolerance -> flu-like -> food-intolerance -> none
        pattern_sequence = [0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 0, 0]
        
        start_date = datetime.utcnow() - timedelta(days=days_per_user)
        
        for day in range(days_per_user):
            # Determine pattern based on position in sequence
            pattern_idx = pattern_sequence[day % len(pattern_sequence)]
            pattern = symptom_types[pattern_idx]
            
            # Add some randomness - occasionally skip a day or change pattern
            if random.random() < 0.2:  # 20% chance to skip
                continue
                
            if random.random() < 0.1:  # 10% chance to change pattern
                pattern_idx = random.choice([i for i in range(len(symptom_types)) if i != pattern_idx])
                pattern = symptom_types[pattern_idx]
            
            # Create symptom log
            symptoms = pattern["symptoms"].copy()
            
            # Add some random additional symptoms occasionally
            if random.random() < 0.3:  # 30% chance
                additional = random.choice(["fatigue", "sore throat", "cough", "dizziness"])
                symptoms.append(additional)
            
            # Vary severity within the pattern's range
            severity = random.randint(pattern["severity"][0], pattern["severity"][1])
            
            # Create the log
            log_date = start_date + timedelta(days=day)
            
            # Create a SymptomLogCreate object
            symptom_log = models.SymptomLog(
                user_id=user.id,
                symptoms=symptoms,
                severity=severity,
                timestamp=log_date,
                ai_classification=pattern["classification"],
                needs_medical_attention=severity >= 8
            )
            
            db.add(symptom_log)
        
        # Commit after each user
        db.commit()
    
    print("Synthetic data generation complete!")

def train_model():
    """Train the symptom prediction model"""
    db = SessionLocal()
    try:
        # Check if we have enough symptom data
        symptom_count = db.query(models.SymptomLog).count()
        print(f"Found {symptom_count} symptom logs in the database")
        
        if symptom_count < 100:  # Arbitrary threshold
            print("Not enough real data, generating synthetic data...")
            generate_synthetic_data(db)
        
        # Get all users with symptom logs
        users_with_symptoms = db.query(models.SymptomLog.user_id).distinct().all()
        user_ids = [user[0] for user in users_with_symptoms]
        
        if not user_ids:
            print("No users with symptom data found. Cannot train model.")
            return
        
        print(f"Training model with data from {len(user_ids)} users...")
        result = symptom_predictor.train_model(db, user_ids)
        
        if result["success"]:
            print(f"Model trained successfully!")
            print(f"Accuracy: {result['accuracy']:.4f}")
            print(f"Validation Accuracy: {result['val_accuracy']:.4f}")
            print(f"Epochs trained: {result['epochs_trained']}")
        else:
            print(f"Model training failed: {result['message']}")
    
    finally:
        db.close()

def test_prediction():
    """Test the prediction functionality"""
    db = SessionLocal()
    try:
        # Get a random user with symptom logs
        user = db.query(models.SymptomLog.user_id).first()
        if not user:
            print("No users with symptom data found. Cannot test prediction.")
            return
        
        user_id = user[0]
        print(f"Testing prediction for user {user_id}...")
        
        # Load the model
        if not symptom_predictor.load_model():
            print("Model not found. Train the model first.")
            return
        
        # Make predictions
        predictions = symptom_predictor.predict_future_symptoms(db, user_id, days_ahead=5)
        
        if "error" in predictions[0]:
            print(f"Prediction error: {predictions[0]['error']}")
            return
        
        print("\nPredicted symptoms for the next 5 days:")
        for pred in predictions:
            print(f"Date: {pred['date']}")
            print(f"  Predicted classification: {pred['predicted_classification']}")
            print(f"  Confidence: {pred['confidence']:.2f}")
            print(f"  Possible symptoms: {', '.join(pred['possible_symptoms'])}")
            print()
        
        # Test pattern analysis
        print("\nAnalyzing symptom patterns...")
        analysis = symptom_predictor.analyze_symptom_patterns(db, user_id)
        
        if "message" in analysis:
            print(f"Analysis message: {analysis['message']}")
            return
        
        print(f"Total symptom logs analyzed: {analysis['total_logs']}")
        print("Symptom frequency:")
        for symptom, count in analysis['symptom_frequency'].items():
            print(f"  {symptom}: {count}")
        
        print(f"Severity trend: {analysis['severity_trend']['trend']}")
        
        print("Insights:")
        for insight in analysis['insights']:
            print(f"  - {insight}")
        
        print("Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
    
    finally:
        db.close()

if __name__ == "__main__":
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_prediction()
    else:
        train_model()
        test_prediction()