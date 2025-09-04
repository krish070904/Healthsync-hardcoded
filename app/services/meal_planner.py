# app/services/meal_planner.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import datetime as dt
from sqlalchemy.orm import Session
from .. import models, schemas, crud
from ..models import MealRecommendation

# Function to calculate age from date of birth
def calculate_age(dob_str):
    try:
        # Try to parse the date string
        if isinstance(dob_str, str):
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d')
            except ValueError:
                # Default to a reasonable age if parsing fails
                return 30
        else:
            # If not a string, use default
            return 30
            
        # Calculate age
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return max(18, age)  # Ensure minimum age of 18
    except Exception:
        # Return a default age if any error occurs
        return 30

# Constants for nutritional requirements
MACRO_RATIOS = {
    "balanced": {"protein": 0.3, "carbs": 0.4, "fat": 0.3},
    "high_protein": {"protein": 0.4, "carbs": 0.3, "fat": 0.3},
    "low_carb": {"protein": 0.35, "carbs": 0.25, "fat": 0.4},
    "keto": {"protein": 0.3, "carbs": 0.1, "fat": 0.6},
}

MEAL_DISTRIBUTION = {
    "standard": {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10},
    "intermittent_fasting": {"breakfast": 0.0, "lunch": 0.45, "dinner": 0.45, "snack": 0.10},
    "six_small_meals": {"breakfast": 0.15, "morning_snack": 0.10, "lunch": 0.25, 
                       "afternoon_snack": 0.10, "dinner": 0.25, "evening_snack": 0.15},
}

# Harris-Benedict or Mifflin-St Jeor formula for BMR calculation
def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int, formula: str = "mifflin") -> float:
    """Calculate Basal Metabolic Rate using either Mifflin-St Jeor or Harris-Benedict formula"""
    gender = gender.lower()
    
    if formula == "mifflin":
        if gender in ("m", "male"):
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    elif formula == "harris-benedict":
        if gender in ("m", "male"):
            bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    else:
        raise ValueError(f"Unknown formula: {formula}. Use 'mifflin' or 'harris-benedict'.")
        
    return bmr

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure based on activity level"""
    activity_multipliers = {
        "sedentary": 1.2,  # Little or no exercise
        "light": 1.375,   # Light exercise 1-3 days/week
        "moderate": 1.55, # Moderate exercise 3-5 days/week
        "active": 1.725,  # Hard exercise 6-7 days/week
        "very_active": 1.9 # Very hard exercise & physical job or 2x training
    }
    
    multiplier = activity_multipliers.get(activity_level.lower(), 1.2)
    return bmr * multiplier

def calculate_nutrient_requirements(tdee: float, macro_profile: str = "balanced") -> Dict[str, float]:
    """Calculate macronutrient requirements based on TDEE and chosen profile"""
    # Get macro ratio profile
    ratios = MACRO_RATIOS.get(macro_profile, MACRO_RATIOS["balanced"])
    
    # Calculate grams of each macronutrient
    # Protein: 4 calories per gram
    # Carbs: 4 calories per gram
    # Fat: 9 calories per gram
    protein_calories = tdee * ratios["protein"]
    carbs_calories = tdee * ratios["carbs"]
    fat_calories = tdee * ratios["fat"]
    
    return {
        "calories": tdee,
        "protein_g": protein_calories / 4,
        "carbs_g": carbs_calories / 4,
        "fat_g": fat_calories / 9,
        "fiber_g": 14 * (tdee / 1000)  # Roughly 14g per 1000 calories
    }

def adjust_for_goal(nutrient_reqs: Dict[str, float], goal: str) -> Dict[str, float]:
    """Adjust nutrient requirements based on fitness goal"""
    adjustments = {
        "weight_loss": 0.8,      # 20% deficit
        "maintenance": 1.0,      # No change
        "muscle_gain": 1.1,      # 10% surplus
        "extreme_loss": 0.7,     # 30% deficit (not recommended long term)
        "extreme_gain": 1.2      # 20% surplus
    }
    
    factor = adjustments.get(goal.lower(), 1.0)
    
    # Adjust calories and macros
    adjusted = {}
    for key, value in nutrient_reqs.items():
        if key != "protein_g":  # Often protein is kept high even in deficit
            adjusted[key] = value * factor
        else:
            # For weight loss, keep protein higher to preserve muscle
            if goal.lower() == "weight_loss" or goal.lower() == "extreme_loss":
                adjusted[key] = max(value, nutrient_reqs["protein_g"])
            else:
                adjusted[key] = value * factor
    
    return adjusted

def filter_foods_for_user(df: pd.DataFrame, user_profile: Dict) -> pd.DataFrame:
    """Filter foods based on user allergies, preferences, and health conditions"""
    # Start with all foods
    filtered_df = df.copy()
    
    # Filter allergies
    if user_profile.get("allergies"):
        allergies = [a.lower() for a in user_profile["allergies"]]
        # Filter where any allergy string appears in tags or name
        allergy_mask = filtered_df.apply(
            lambda r: not any(a in str(r.get('tags', '')).lower() or 
                             a in str(r.get('name', '')).lower() 
                             for a in allergies), 
            axis=1
        )
        filtered_df = filtered_df[allergy_mask].reset_index(drop=True)
    
    # Filter based on health conditions
    if user_profile.get("diseases"):
        diseases = [d.lower() for d in user_profile["diseases"]]
        
        # Example disease-specific filtering
        if "diabetes" in diseases:
            # For diabetes, filter out high glycemic index foods if tagged
            diabetes_mask = filtered_df.apply(
                lambda r: "high_gi" not in str(r.get('tags', '')).lower(),
                axis=1
            )
            filtered_df = filtered_df[diabetes_mask].reset_index(drop=True)
            
        if "hypertension" in diseases:
            # For hypertension, filter out high sodium foods if tagged
            hypertension_mask = filtered_df.apply(
                lambda r: "high_sodium" not in str(r.get('tags', '')).lower(),
                axis=1
            )
            filtered_df = filtered_df[hypertension_mask].reset_index(drop=True)
    
    # Apply user preferences
    if user_profile.get("preferences") and isinstance(user_profile["preferences"], dict):
        prefs = user_profile["preferences"]
        
        # Handle diet type preferences
        if prefs.get("diet_type"):
            diet = prefs["diet_type"].lower()
            if diet == "vegetarian":
                veg_mask = filtered_df.apply(
                    lambda r: "meat" not in str(r.get('tags', '')).lower() and 
                              "fish" not in str(r.get('tags', '')).lower(),
                    axis=1
                )
                filtered_df = filtered_df[veg_mask].reset_index(drop=True)
            elif diet == "vegan":
                vegan_mask = filtered_df.apply(
                    lambda r: not any(tag in str(r.get('tags', '')).lower() 
                                     for tag in ["meat", "fish", "dairy", "egg"]),
                    axis=1
                )
                filtered_df = filtered_df[vegan_mask].reset_index(drop=True)
    
    return filtered_df

def score_foods_for_meal(df: pd.DataFrame, meal_type: str, target_nutrients: Dict[str, float]) -> pd.DataFrame:
    """Score foods based on nutritional value and appropriateness for meal type"""
    # Add scoring columns
    df = df.copy()
    
    # Calculate calories per gram
    df['cal_per_g'] = df['calories_per_100g'] / 100.0
    
    # Base nutritional score - protein density and fiber estimation
    df['protein_density'] = df['protein_g_per_100g'] / df['calories_per_100g'].replace(0, 1)
    # Estimate fiber from carbs (simplified)
    df['estimated_fiber'] = df['carbs_g_per_100g'] * 0.1  # Rough estimate
    
    # Meal-specific scoring
    if meal_type == "breakfast":
        # Breakfast favors moderate protein, higher carbs, moderate fat
        df['meal_score'] = (
            df['protein_density'] * 0.3 + 
            (df['carbs_g_per_100g'] / df['calories_per_100g'].replace(0, 1)) * 0.5 +
            (df['estimated_fiber'] / df['calories_per_100g'].replace(0, 1)) * 0.2
        )
    elif meal_type == "lunch" or meal_type == "dinner":
        # Lunch/dinner favor higher protein, moderate carbs, moderate fat
        df['meal_score'] = (
            df['protein_density'] * 0.5 + 
            (df['carbs_g_per_100g'] / df['calories_per_100g'].replace(0, 1)) * 0.2 +
            (df['estimated_fiber'] / df['calories_per_100g'].replace(0, 1)) * 0.3
        )
    else:  # snack
        # Snacks favor protein and fiber, lower calories
        df['meal_score'] = (
            df['protein_density'] * 0.4 + 
            (df['estimated_fiber'] / df['calories_per_100g'].replace(0, 1)) * 0.6
        )
    
    # Sort by meal score
    return df.sort_values('meal_score', ascending=False).reset_index(drop=True)

def generate_meal(df: pd.DataFrame, target_calories: float, max_items: int = 4) -> Tuple[List[Dict], Dict]:
    """Generate a balanced meal targeting specific calories with TOPSIS ranking"""
    if df.empty:
        return [], {"protein_g": 0, "carbs_g": 0, "fat_g": 0, "calories": 0}
    
    # TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)
    # Step 1: Create decision matrix with normalized values
    decision_matrix = df[['protein_density', 'estimated_fiber', 'meal_score']].values
    
    # Step 2: Normalize the decision matrix
    norm = np.sqrt(np.sum(decision_matrix**2, axis=0))
    normalized_matrix = decision_matrix / norm
    
    # Step 3: Define weights for criteria
    weights = np.array([0.4, 0.3, 0.3])  # protein_density, fiber, meal_score
    
    # Step 4: Calculate weighted normalized decision matrix
    weighted_matrix = normalized_matrix * weights
    
    # Step 5: Determine ideal and negative-ideal solutions
    ideal_best = np.max(weighted_matrix, axis=0)
    ideal_worst = np.min(weighted_matrix, axis=0)
    
    # Step 6: Calculate separation measures
    s_best = np.sqrt(np.sum((weighted_matrix - ideal_best)**2, axis=1))
    s_worst = np.sqrt(np.sum((weighted_matrix - ideal_worst)**2, axis=1))
    
    # Step 7: Calculate performance score
    performance = s_worst / (s_best + s_worst)
    
    # Add performance score to dataframe
    df = df.copy()
    df['topsis_score'] = performance
    
    # Sort by TOPSIS score
    df_sorted = df.sort_values('topsis_score', ascending=False).reset_index(drop=True)
    
    # Select foods for the meal
    selected_items = []
    remaining_calories = target_calories
    total_nutrition = {"protein_g": 0, "carbs_g": 0, "fat_g": 0, "calories": 0}
    
    for _, food in df_sorted.iterrows():
        if len(selected_items) >= max_items or remaining_calories <= 20:
            break
            
        # Calculate appropriate serving size
        cal_per_g = food['calories_per_100g'] / 100.0
        max_serving = min(food.get('serving_g', 100), remaining_calories / cal_per_g)
        serving_size = max(20, min(max_serving, remaining_calories * 0.4 / cal_per_g))
        
        calories = serving_size * cal_per_g
        protein = serving_size * food['protein_g_per_100g'] / 100
        carbs = serving_size * food['carbs_g_per_100g'] / 100
        fat = serving_size * food['fat_g_per_100g'] / 100
        
        if calories > 20:  # Only add if it contributes meaningful calories
            selected_items.append({
                "name": food['name'],
                "grams": int(serving_size),
                "calories": int(calories),
                "protein_g": round(protein, 1),
                "carbs_g": round(carbs, 1),
                "fat_g": round(fat, 1)
            })
            
            # Update remaining calories and nutrition totals
            remaining_calories -= calories
            total_nutrition["protein_g"] += protein
            total_nutrition["carbs_g"] += carbs
            total_nutrition["fat_g"] += fat
            total_nutrition["calories"] += calories
    
    # Round nutrition values
    for key in total_nutrition:
        if key == "calories":
            total_nutrition[key] = int(total_nutrition[key])
        else:
            total_nutrition[key] = round(total_nutrition[key], 1)
    
    return selected_items, total_nutrition

def generate_meal_plan(user_profile: Dict, food_df: pd.DataFrame, 
                      distribution_type: str = "standard") -> Dict:
    """Generate a complete meal plan based on user profile and nutritional needs"""
    # Calculate BMR and TDEE
    bmr = calculate_bmr(
        gender=user_profile.get("gender", "male"),
        weight_kg=user_profile.get("weight_kg", 70),
        height_cm=user_profile.get("height_cm", 170),
        age=user_profile.get("age", 30)
    )
    
    activity_level = user_profile.get("activity_level", "moderate")
    tdee = calculate_tdee(bmr, activity_level)
    
    # Get macro profile from user preferences or default to balanced
    macro_profile = "balanced"
    if user_profile.get("preferences") and isinstance(user_profile["preferences"], dict):
        macro_profile = user_profile["preferences"].get("macro_profile", "balanced")
    
    # Calculate nutrient requirements
    nutrient_reqs = calculate_nutrient_requirements(tdee, macro_profile)
    
    # Adjust for goal if specified
    goal = "maintenance"
    if user_profile.get("preferences") and isinstance(user_profile["preferences"], dict):
        goal = user_profile["preferences"].get("goal", "maintenance")
    
    adjusted_reqs = adjust_for_goal(nutrient_reqs, goal)
    
    # Filter foods based on user profile
    filtered_foods = filter_foods_for_user(food_df, user_profile)
    
    # Get meal distribution
    meal_dist = MEAL_DISTRIBUTION.get(distribution_type, MEAL_DISTRIBUTION["standard"])
    
    # Generate meals
    plan = {}
    for meal_type, fraction in meal_dist.items():
        target_calories = int(adjusted_reqs["calories"] * fraction)
        
        # Score foods for this specific meal type
        scored_foods = score_foods_for_meal(filtered_foods, meal_type, adjusted_reqs)
        
        # Generate the meal
        meal_items, nutrition = generate_meal(scored_foods, target_calories)
        
        plan[meal_type] = {
            "target_calories": target_calories,
            "items": meal_items,
            "total_calories": nutrition["calories"],
            "nutrition": nutrition
        }
    
    # Add plan summary
    plan["daily_calories_target"] = int(adjusted_reqs["calories"])
    plan["daily_protein_target"] = round(adjusted_reqs["protein_g"], 1)
    plan["daily_carbs_target"] = round(adjusted_reqs["carbs_g"], 1)
    plan["daily_fat_target"] = round(adjusted_reqs["fat_g"], 1)
    
    # Calculate actual totals
    daily_totals = {
        "calories": sum(plan[m]["total_calories"] for m in meal_dist.keys()),
        "protein_g": sum(plan[m]["nutrition"]["protein_g"] for m in meal_dist.keys()),
        "carbs_g": sum(plan[m]["nutrition"]["carbs_g"] for m in meal_dist.keys()),
        "fat_g": sum(plan[m]["nutrition"]["fat_g"] for m in meal_dist.keys())
    }
    
    plan["daily_totals"] = daily_totals
    
    return plan



def generate_daily_meal_plan(user_profile: Dict, food_df: pd.DataFrame, nutrient_reqs: Dict[str, float]) -> Dict:
    """Generate a complete daily meal plan based on user profile and nutritional requirements"""
    # Get meal distribution type from user preferences or default to standard
    distribution_type = "standard"
    if user_profile.get("preferences") and isinstance(user_profile["preferences"], dict):
        distribution_type = user_profile["preferences"].get("meal_distribution", "standard")
    
    # Filter foods based on user profile
    filtered_foods = filter_foods_for_user(food_df, user_profile)
    
    # Get meal distribution
    meal_dist = MEAL_DISTRIBUTION.get(distribution_type, MEAL_DISTRIBUTION["standard"])
    
    # Generate meals
    plan = {}
    for meal_type, fraction in meal_dist.items():
        target_calories = int(nutrient_reqs["calories"] * fraction)
        
        # Score foods for this specific meal type
        scored_foods = score_foods_for_meal(filtered_foods, meal_type, nutrient_reqs)
        
        # Generate the meal
        meal_items, nutrition = generate_meal(scored_foods, target_calories)
        
        plan[meal_type] = {
            "target_calories": target_calories,
            "items": meal_items,
            "total_calories": nutrition["calories"],
            "nutrition": nutrition
        }
    
    # Add plan summary
    plan["daily_calories_target"] = int(nutrient_reqs["calories"])
    plan["daily_protein_target"] = round(nutrient_reqs["protein_g"], 1)
    plan["daily_carbs_target"] = round(nutrient_reqs["carbs_g"], 1)
    plan["daily_fat_target"] = round(nutrient_reqs["fat_g"], 1)
    
    # Calculate actual totals
    daily_totals = {
        "calories": sum(plan[m]["total_calories"] for m in meal_dist.keys()),
        "protein_g": sum(plan[m]["nutrition"]["protein_g"] for m in meal_dist.keys()),
        "carbs_g": sum(plan[m]["nutrition"]["carbs_g"] for m in meal_dist.keys()),
        "fat_g": sum(plan[m]["nutrition"]["fat_g"] for m in meal_dist.keys())
    }
    
    plan["daily_totals"] = daily_totals
    
    return plan

def generate_recommendations(meal_plan: Dict, user_profile: Dict, nutrient_reqs: Dict[str, float]) -> List[str]:
    """Generate personalized recommendations based on the meal plan, user profile, and nutrient requirements"""
    recommendations = []
    
    # Check if calories are sufficient
    daily_target = meal_plan.get("daily_calories_target", 0)
    daily_total = meal_plan.get("daily_totals", {}).get("calories", 0)
    
    if daily_total < daily_target * 0.9:
        recommendations.append(f"Your meal plan is {daily_target - daily_total} calories below your target. "
                              f"Consider adding more food to reach your {daily_target} calorie goal.")
    
    # Check protein intake
    protein_target = meal_plan.get("daily_protein_target", 0)
    protein_total = meal_plan.get("daily_totals", {}).get("protein_g", 0)
    
    if protein_total < protein_target * 0.8:
        recommendations.append(f"Your protein intake is below target. Aim for {protein_target}g of protein daily "
                              f"to support your goals.")
    
    # Check for health conditions
    if user_profile.get("diseases"):
        diseases = [d.lower() for d in user_profile["diseases"]]
        
        if "diabetes" in diseases:
            carbs_total = meal_plan.get("daily_totals", {}).get("carbs_g", 0)
            if carbs_total > 150:  # Example threshold
                recommendations.append("Consider reducing your carbohydrate intake and focusing on low-glycemic "
                                     "options to better manage blood sugar levels.")
        
        if "hypertension" in diseases:
            recommendations.append("Remember to limit sodium intake. Consider using herbs and spices "
                                 "instead of salt to flavor your meals.")
    
    # Add general recommendations
    recommendations.append("Stay hydrated by drinking at least 8 glasses of water daily.")
    
    if user_profile.get("preferences", {}).get("goal") == "weight_loss":
        recommendations.append("Include regular physical activity along with your meal plan for optimal results.")
    
    return recommendations

# Functions for meal recommendation storage and retrieval
def save_meal_recommendation(db: Session, user_id: str, meal_plan: Dict[str, Any], 
                             nutrient_reqs: Dict[str, float], criteria_weights: Dict[str, float] = None) -> models.MealRecommendation:
    """Save a meal recommendation to the database"""
    # Extract nutritional totals from meal plan
    daily_totals = meal_plan.get("daily_totals", {})
    
    # Create recommendation data
    recommendation_data = schemas.MealRecommendationCreate(
        user_id=user_id,
        daily_calories_target=int(nutrient_reqs.get("calories", 0)),
        protein_target_g=int(nutrient_reqs.get("protein_g", 0)),
        carbs_target_g=int(nutrient_reqs.get("carbs_g", 0)),
        fat_target_g=int(nutrient_reqs.get("fat_g", 0)),
        meal_plan=meal_plan,
        total_calories=int(daily_totals.get("calories", 0)),
        total_protein_g=float(daily_totals.get("protein_g", 0)),
        total_carbs_g=float(daily_totals.get("carbs_g", 0)),
        total_fat_g=float(daily_totals.get("fat_g", 0)),
        algorithm_version="1.0",
        criteria_weights=criteria_weights
    )
    
    # Save to database
    return crud.create_meal_recommendation(db, recommendation_data)

def get_user_meal_recommendation_history(db: Session, user_id: str, limit: int = 10) -> List[models.MealRecommendation]:
    """Get a user's meal recommendation history"""
    return crud.get_user_meal_recommendations(db, user_id, limit)

def update_recommendation_with_feedback(db: Session, recommendation_id: str, 
                                       rating: int = None, followed: bool = None, 
                                       feedback: str = None, symptoms: List[str] = None) -> models.MealRecommendation:
    """Update a meal recommendation with user feedback"""
    update_data = schemas.MealRecommendationUpdate(
        user_rating=rating,
        user_followed=followed,
        user_feedback=feedback,
        symptoms_reported=symptoms,
        followed_at=datetime.utcnow() if followed else None
    )
    
    return crud.update_meal_recommendation(db, recommendation_id, update_data)

def calculate_age(dob_str: str) -> int:
    """Calculate age from date of birth string"""
    try:
        # Try to parse the date string
        if not dob_str:
            return 30  # Default age if no DOB provided
            
        # Handle different date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                dob = datetime.strptime(dob_str, fmt)
                today = datetime.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                return max(18, min(age, 80))  # Ensure age is between 18 and 80
            except ValueError:
                continue
                
        # If all formats fail, return default
        return 30
    except Exception:
        # Return a reasonable default if any error occurs
        return 30

def generate_meal_plan_with_tracking(db: Session, user_id: str, user_profile: Dict, 
                                    food_df: pd.DataFrame, goal: str = "maintenance",
                                    macro_profile: str = "balanced") -> Dict[str, Any]:
    """Generate a meal plan and save it to the recommendation history"""
    # Calculate user's nutritional requirements
    age = calculate_age(user_profile.get("dob", "2000-01-01"))
    bmr = calculate_bmr(
        gender=user_profile.get("gender", "male"),
        weight_kg=user_profile.get("weight_kg", 70),
        height_cm=user_profile.get("height_cm", 170),
        age=age
    )
    
    activity_level = user_profile.get("preferences", {}).get("activity_level", "moderate")
    tdee = calculate_tdee(bmr, activity_level)
    
    # Calculate nutrient requirements
    nutrient_reqs = calculate_nutrient_requirements(tdee, macro_profile)
    nutrient_reqs = adjust_for_goal(nutrient_reqs, goal)
    
    # Generate meal plan
    meal_plan = generate_daily_meal_plan(
        user_profile=user_profile,
        food_df=food_df,
        nutrient_reqs=nutrient_reqs
    )
    
    # Add recommendations
    meal_plan["recommendations"] = generate_recommendations(meal_plan, user_profile, nutrient_reqs)
    
    # Save to database
    criteria_weights = {
        "protein_density": 0.4,
        "nutrient_balance": 0.3,
        "meal_appropriateness": 0.3
    }
    recommendation = save_meal_recommendation(db, user_id, meal_plan, nutrient_reqs, criteria_weights)
    
    # Add recommendation ID to the meal plan for reference
    meal_plan["recommendation_id"] = recommendation.id
    
    return meal_plan