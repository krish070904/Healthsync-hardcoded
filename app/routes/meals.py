from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, auth
from ..db import get_db
from typing import List, Dict, Any
import pandas as pd
from ..services import meal_planner
from ..models import User

router = APIRouter(prefix="/meals", tags=["meals"])

@router.post("/log", response_model=schemas.MealLogResponse)
def log_meal(meal_log: schemas.MealLogCreate, db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_active_user)):
    """Log a meal and track symptoms after eating"""
    # Validate user exists
    user = crud.get_user(db, meal_log.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate meal type
    valid_meal_types = ["breakfast", "lunch", "dinner", "snack"]
    if meal_log.meal_type not in valid_meal_types:
        raise HTTPException(status_code=400, detail=f"Meal type must be one of: {valid_meal_types}")
    
    # Create meal log
    result = crud.create_meal_log(db, meal_log)
    
    # If symptoms are reported after meal, create a symptom log
    if meal_log.symptoms_after:
        symptom_log = schemas.SymptomLogCreate(
            user_id=meal_log.user_id,
            symptoms=meal_log.symptoms_after,
            severity=5  # Default severity for food-related symptoms
        )
        crud.create_symptom_log(db, symptom_log)
    
    return result

@router.get("/user/{user_id}", response_model=List[schemas.MealLogResponse])
def get_user_meals(user_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get user's meal history"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud.get_user_meals(db, user_id, days)

@router.get("/user/{user_id}/nutrition-summary")
def get_nutrition_summary(user_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get nutrition summary for user's recent meals"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    meals = crud.get_user_meals(db, user_id, days)
    
    if not meals:
        return {"message": "No recent meals to analyze"}
    
    # Calculate nutrition totals
    total_calories = sum(meal.total_calories for meal in meals)
    avg_calories_per_day = total_calories / days
    
    # Count meals by type
    meal_counts = {}
    for meal in meals:
        meal_counts[meal.meal_type] = meal_counts.get(meal.meal_type, 0) + 1
    
    # Analyze food patterns
    all_foods = []
    for meal in meals:
        for food in meal.foods:
            if isinstance(food, dict) and 'name' in food:
                all_foods.append(food['name'])
    
    from collections import Counter
    food_counts = Counter(all_foods)
    most_eaten_foods = food_counts.most_common(5)
    
    # Check for symptoms after meals
    meals_with_symptoms = [meal for meal in meals if meal.symptoms_after]
    
    summary = {
        "total_meals_logged": len(meals),
        "total_calories": total_calories,
        "average_calories_per_day": round(avg_calories_per_day, 2),
        "meal_distribution": meal_counts,
        "most_eaten_foods": most_eaten_foods,
        "meals_with_symptoms": len(meals_with_symptoms),
        "recommendations": []
    }
    
    # Generate recommendations
    if avg_calories_per_day < 1200:
        summary["recommendations"].append("Consider increasing daily calorie intake")
    elif avg_calories_per_day > 3000:
        summary["recommendations"].append("Consider reducing daily calorie intake")
    
    if len(meals_with_symptoms) > len(meals) * 0.3:  # More than 30% of meals cause symptoms
        summary["recommendations"].append("Many meals are causing symptoms. Consider consulting a nutritionist.")
    
    return summary

@router.post("/recommendations/generate", response_model=schemas.MealPlanResponse)
def generate_meal_recommendation(recommendation_request: schemas.MealRecommendationRequest, db: Session = Depends(get_db)):
    user_id = recommendation_request.user_id
    goal = recommendation_request.goal if recommendation_request.goal else "maintenance"
    macro_profile = recommendation_request.macro_profile if recommendation_request.macro_profile else "balanced"
    """Generate a personalized meal recommendation and save it to history"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate goal and macro profile
    valid_goals = ["weight_loss", "maintenance", "muscle_gain", "extreme_loss", "extreme_gain"]
    if goal not in valid_goals:
        raise HTTPException(status_code=400, detail=f"Goal must be one of: {valid_goals}")
    
    valid_profiles = ["balanced", "high_protein", "low_carb", "keto"]
    if macro_profile not in valid_profiles:
        raise HTTPException(status_code=400, detail=f"Macro profile must be one of: {valid_profiles}")
    
    # Load food database
    try:
        food_df = pd.read_csv("app/data/food_database.csv")
    except Exception as e:
        # Fallback to a smaller dataset if main one fails
        try:
            food_df = pd.read_csv("app/data/sample_foods.csv")
        except:
            raise HTTPException(status_code=500, detail="Could not load food database")
    
    # Create user profile from user model
    user_profile = {
        "name": user.full_name if hasattr(user, 'full_name') else user.username,
        "gender": user.gender,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "allergies": user.allergies,
        "medical_conditions": user.medical_conditions,
        "preferences": {}
    }
    
    # Add goal to preferences if not already there
    if "preferences" not in user_profile or not isinstance(user_profile["preferences"], dict):
        user_profile["preferences"] = {}
    user_profile["preferences"]["goal"] = goal
    
    # Generate meal plan with tracking
    meal_plan = meal_planner.generate_meal_plan_with_tracking(
        db=db,
        user_id=user_id,
        user_profile=user_profile,
        food_df=food_df,
        goal=goal,
        macro_profile=macro_profile
    )
    
    # Format response
    return {
        "user_id": user_id,
        "daily_calories_target": meal_plan.get("daily_calories_target", 0),
        "meals": meal_plan.get("meals", {}),
        "recommendations": meal_plan.get("recommendations", [])
    }

@router.get("/recommendations/history/{user_id}", response_model=List[schemas.MealRecommendationResponse])
def get_meal_recommendation_history(user_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get a user's meal recommendation history"""
    # Validate user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return meal_planner.get_user_meal_recommendation_history(db, user_id, limit)

@router.post("/recommendations/{recommendation_id}/feedback")
def provide_recommendation_feedback(recommendation_id: str, rating: int = None, 
                                  followed: bool = None, feedback: str = None,
                                  symptoms: List[str] = None, db: Session = Depends(get_db)):
    """Provide feedback on a meal recommendation"""
    # Validate recommendation exists
    recommendation = crud.get_meal_recommendation(db, recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Meal recommendation not found")
    
    # Validate rating if provided
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Update recommendation with feedback
    updated_rec = meal_planner.update_recommendation_with_feedback(
        db=db,
        recommendation_id=recommendation_id,
        rating=rating,
        followed=followed,
        feedback=feedback,
        symptoms=symptoms
    )
    
    return {"status": "success", "message": "Feedback recorded successfully"}

@router.get("/user/{user_id}/food-correlations")
def analyze_food_symptom_correlations(user_id: str, db: Session = Depends(get_db)):
    """Analyze correlations between foods and symptoms"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    meals = crud.get_user_meals(db, user_id, days=30)
    
    if not meals:
        return {"message": "No recent meals to analyze"}
    
    # Create food-symptom correlation data
    food_symptom_data = {}
    
    for meal in meals:
        if meal.symptoms_after:  # Only analyze meals that caused symptoms
            for food in meal.foods:
                if isinstance(food, dict) and 'name' in food:
                    food_name = food['name']
                    if food_name not in food_symptom_data:
                        food_symptom_data[food_name] = {
                            'total_occurrences': 0,
                            'symptom_occurrences': 0,
                            'symptoms': []
                        }
                    
                    food_symptom_data[food_name]['total_occurrences'] += 1
                    food_symptom_data[food_name]['symptom_occurrences'] += 1
                    food_symptom_data[food_name]['symptoms'].extend(meal.symptoms_after)
    
    # Calculate correlation scores
    correlations = []
    for food_name, data in food_symptom_data.items():
        if data['total_occurrences'] >= 2:  # Only consider foods eaten multiple times
            correlation_score = data['symptom_occurrences'] / data['total_occurrences']
            most_common_symptoms = Counter(data['symptoms']).most_common(3)
            
            correlations.append({
                'food': food_name,
                'correlation_score': round(correlation_score, 2),
                'total_occurrences': data['total_occurrences'],
                'symptom_occurrences': data['symptom_occurrences'],
                'most_common_symptoms': most_common_symptoms
            })
    
    # Sort by correlation score (highest first)
    correlations.sort(key=lambda x: x['correlation_score'], reverse=True)
    
    return {
        "food_symptom_correlations": correlations[:10],  # Top 10 correlations
        "high_risk_foods": [c for c in correlations if c['correlation_score'] > 0.5]
    }
