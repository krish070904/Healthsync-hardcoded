# app/services/symptom_predictor.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from random import choice, random

from .. import crud, models, schemas

# Constants
SYMPTOM_FEATURES = ['fever', 'nausea', 'bloating', 'headache']

class SymptomPredictor:
    """Mock symptom predictor for testing without TensorFlow"""
    def __init__(self):
        self.is_model_loaded = True
        print("Using mock symptom predictor for testing")
        
    def load_model(self):
        """Mock model loading for testing"""
        self.is_model_loaded = True
        return True
        
    def preprocess_symptom_data(self, db: Session, user_id: str, days: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """Mock preprocessing for testing"""
        # Get user's symptom history
        symptoms = crud.get_user_symptoms(db, user_id, days=days)
        
        if not symptoms:
            return None, None
        
        # For mock implementation, just return dummy data
        return np.array([1]), np.array([1])
    
    def _create_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Mock sequence creation for testing"""
        return np.array([1]), np.array([1])
        
    def predict(self, db: Session, user_id: str, days_to_predict: int = 7) -> List[Dict[str, Any]]:
        """Mock prediction for testing"""
        predictions = []
        
        # Generate mock predictions
        for i in range(days_to_predict):
            pred_date = datetime.now() + timedelta(days=i+1)
            pred_class = choice(["flu-like", "food-intolerance", "none"])
            pred_confidence = random() * 0.5 + 0.5  # Random confidence between 0.5 and 1.0
            
            predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "predicted_classification": pred_class,
                "confidence": pred_confidence,
                "possible_symptoms": self._suggest_possible_symptoms(pred_class)
            })
        
        return predictions
    
    def _suggest_possible_symptoms(self, classification: str) -> List[str]:
        """Suggest possible symptoms based on the predicted classification"""
        if classification == "flu-like":
            return ["fever", "headache", "body aches", "fatigue"]
        elif classification == "food-intolerance":
            return ["nausea", "bloating", "stomach pain", "indigestion"]
        else:  # "none"
            return []
    
    def analyze_symptom_patterns(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Mock symptom pattern analysis for testing"""
        return {
            "message": "Symptom pattern analysis",
            "common_symptoms": ["headache", "nausea"],
            "symptom_frequency": {"headache": 0.7, "nausea": 0.4},
            "severity_trend": "decreasing",
            "possible_triggers": ["stress", "certain foods"]
        }
    
    def train_model(self, db: Session, user_ids: List[str], epochs: int = 50, batch_size: int = 32) -> Dict[str, Any]:
        """Mock training function for testing"""
        return {"success": True, "message": "Mock model training completed"}

# Create an instance of the predictor
symptom_predictor = SymptomPredictor()