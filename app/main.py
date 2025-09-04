from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, crud, schemas, auth
from .db import Base, engine
from .routes import symptoms, meals, alerts, predictions, progress, consultation
import os
import pandas as pd
from math import floor
import logging
import pathlib
from datetime import datetime, timedelta

# Get the current directory
BASE_DIR = pathlib.Path(__file__).parent

# Set up templates with flexible path
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize FastAPI app
app = FastAPI(title="HealthSync API", description="AI-powered health assistant for personalized diet plans and symptom tracking")

# Mount static files with flexible path
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/health")
def health_check():
    return {
        "status": "HealthSync AI Health Assistant is running",
        "version": "1.0.0",
        "features": [
            "Personalized meal planning",
            "Symptom tracking with AI classification",
            "Health alerts and notifications",
            "Progress tracking",
            "Food-symptom correlation analysis",
            "Symptom prediction with LSTM/GRU model",
            "Rule-based health consultation"
        ]
    }

# Add authentication middleware
from .middleware import add_auth_middleware
add_auth_middleware(app)

# Include all route modules
app.include_router(symptoms.router)
app.include_router(meals.router)
app.include_router(alerts.router)
app.include_router(predictions.router)
app.include_router(progress.router)
app.include_router(consultation.router)

# create tables (simple approach)
Base.metadata.create_all(bind=engine)

def get_db():
    from .db import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """Serve the main index HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Serve the registration page"""
    return templates.TemplateResponse("register.html", {"request": request})



@app.post("/users/", response_model=schemas.UserResponse)
async def create_user(u: schemas.UserCreate, session: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = session.query(models.User).filter(models.User.username == u.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = session.query(models.User).filter(models.User.email == u.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = crud.create_user(session, u)
    
    # Send welcome email
    from .services.email_service import send_welcome_email
    try:
        await send_welcome_email(u.email, u.username)
    except Exception as e:
        # Log the error but don't fail registration if email sending fails
        print(f"Failed to send welcome email: {str(e)}")
    
    return user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: str, session: Session = Depends(get_db)):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user
        
@app.get("/predictions", response_class=HTMLResponse)
def get_predictions_page(request: Request):
    """Serve the symptom prediction HTML page"""
    return templates.TemplateResponse("symptom-prediction.html", {"request": request})

@app.get("/progress-tracker", response_class=HTMLResponse)
def get_progress_tracker_page(request: Request):
    """Serve the progress tracker HTML page"""
    return templates.TemplateResponse("progress-tracker.html", {"request": request})

@app.get("/health-consultation", response_class=HTMLResponse)
def get_health_consultation_page(request: Request):
    """Serve the health consultation HTML page"""
    return templates.TemplateResponse("health-consultation.html", {"request": request})

@app.get("/symptoms", response_class=HTMLResponse)
def get_symptoms_page(request: Request):
    """Serve the symptoms tracking HTML page"""
    return templates.TemplateResponse("symptoms.html", {"request": request})

@app.get("/meals", response_class=HTMLResponse)
def get_meals_page(request: Request):
    """Serve the meals planning HTML page"""
    return templates.TemplateResponse("meals.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
def get_profile_page(request: Request):
    """Serve the user profile HTML page"""
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/progress", response_class=HTMLResponse)
def get_progress_page(request: Request):
    """Serve the progress HTML page"""
    return templates.TemplateResponse("progress.html", {"request": request})

@app.get("/alerts", response_class=HTMLResponse)
def get_alerts_page(request: Request):
    """Serve the alerts HTML page"""
    return templates.TemplateResponse("alerts.html", {"request": request})

@app.get("/analysis", response_class=HTMLResponse)
def get_analysis_page(request: Request):
    """Serve the analysis HTML page"""
    return templates.TemplateResponse("analysis.html", {"request": request})

@app.get("/consultation", response_class=HTMLResponse)
def get_consultation_page(request: Request):
    """Serve the consultation HTML page"""
    return templates.TemplateResponse("consultation.html", {"request": request})

@app.post("/food/load_sample")
def load_food_sample(session: Session = Depends(get_db)):
    path = os.path.join("data", "food_sample.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="data/food_sample.csv not found")
    df = pd.read_csv(path)
    crud.bulk_insert_foods_from_df(session, df)
    return {"loaded": len(df), "message": "Sample food data loaded successfully"}

def mifflin_calories(sex, weight_kg, height_cm, age, activity_factor=1.2):
    if sex.lower() in ("m", "male"):
        bmr = 10*weight_kg + 6.25*height_cm - 5*age + 5
    else:
        bmr = 10*weight_kg + 6.25*height_cm - 5*age - 161
    return int(bmr * activity_factor)

@app.get("/generate_plan/{user_id}")
def generate_plan(user_id: str, session: Session = Depends(get_db)):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "user not found")

    u = {
        "sex": user.gender,
        "age": 25,  # TODO: calculate from dob
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "activity_factor": 1.2,
        "allergies": user.allergies or []
    }

    # Get foods with ORM
    foods = session.query(models.FoodItem).all()
    if not foods:
        raise HTTPException(400, "no foods in DB; load sample first")

    df = pd.DataFrame([f.__dict__ for f in foods])
    df = df.drop(columns=["_sa_instance_state"], errors="ignore")

    # Filter allergies
    if u['allergies']:
        al = [a.lower() for a in u['allergies']]
        df = df[~df['tags'].str.lower().apply(lambda txt: any(a in txt for a in al))]

    # Calculate calories
    daily_cal = mifflin_calories(u['sex'], u['weight_kg'], u['height_cm'], u['age'], u['activity_factor'])

    # Generate meal plan using enhanced algorithm
    plan = generate_enhanced_meal_plan(df, daily_cal, u)
    
    # Generate AI recommendations
    recommendations = generate_ai_recommendations(user, session)

    logging.info(f"Generated plan for user {user_id}, target calories {daily_cal}")

    return {
        "user_id": user_id,
        "daily_calories_target": daily_cal,
        "meals": plan,
        "recommendations": recommendations
    }

def generate_enhanced_meal_plan(df, daily_cal, user_profile):
    """Enhanced meal planning with better nutrition balance"""
    # Meal distribution
    meal_distribution = {
        'breakfast': 0.25,
        'lunch': 0.35,
        'dinner': 0.30,
        'snack': 0.10
    }
    
    plan = {}
    
    for meal_type, fraction in meal_distribution.items():
        target_calories = int(daily_cal * fraction)
        meal_items = generate_balanced_meal(df, target_calories, meal_type, user_profile)
        
        total_calories = sum(item['calories'] for item in meal_items)
        
        plan[meal_type] = {
            "target_calories": target_calories,
            "items": meal_items,
            "total_calories": total_calories,
            "nutrition": calculate_meal_nutrition(meal_items, df)
        }
    
    return plan

def generate_balanced_meal(df, target_calories, meal_type, user_profile):
    """Generate a nutritionally balanced meal"""
    # Prioritize different nutrients based on meal type
    if meal_type == "breakfast":
        priority_nutrients = ["protein", "fiber"]
    elif meal_type == "lunch":
        priority_nutrients = ["protein", "carbs", "fiber"]
    elif meal_type == "dinner":
        priority_nutrients = ["protein", "fiber"]
    else:  # snack
        priority_nutrients = ["protein", "fiber"]
    
    # Calculate calories per gram for each food
    df['cal_per_g'] = df['calories_per_100g'] / 100.0
    
    # Score foods based on priority nutrients
    df['nutrition_score'] = 0
    for nutrient in priority_nutrients:
        if nutrient == "protein":
            df['nutrition_score'] += df['protein_g_per_100g'] / df['calories_per_100g'].replace(0, 1)
        elif nutrient == "fiber":
            # Estimate fiber content (simplified)
            df['nutrition_score'] += (df['carbs_g_per_100g'] * 0.1) / df['calories_per_100g'].replace(0, 1)
    
    # Sort by nutrition score
    df_sorted = df.sort_values('nutrition_score', ascending=False)
    
    selected_items = []
    remaining_calories = target_calories
    
    for _, food in df_sorted.iterrows():
        if remaining_calories <= 50:
            break
            
        # Calculate appropriate serving size
        max_serving = min(food['serving_g'], remaining_calories / food['cal_per_g'])
        serving_size = max(20, min(max_serving, remaining_calories * 0.4 / food['cal_per_g']))
        
        calories = serving_size * food['cal_per_g']
        
        if calories > 50:  # Only add if it contributes meaningful calories
            selected_items.append({
                "name": food['name'],
                "grams": int(serving_size),
                "calories": int(calories),
                "protein_g": round(serving_size * food['protein_g_per_100g'] / 100, 1),
                "carbs_g": round(serving_size * food['carbs_g_per_100g'] / 100, 1),
                "fat_g": round(serving_size * food['fat_g_per_100g'] / 100, 1)
            })
            remaining_calories -= calories
    
    return selected_items

def calculate_meal_nutrition(meal_items, df):
    """Calculate total nutrition for a meal"""
    total_protein = sum(item.get('protein_g', 0) for item in meal_items)
    total_carbs = sum(item.get('carbs_g', 0) for item in meal_items)
    total_fat = sum(item.get('fat_g', 0) for item in meal_items)
    
    return {
        "protein_g": round(total_protein, 1),
        "carbs_g": round(total_carbs, 1),
        "fat_g": round(total_fat, 1)
    }

def generate_ai_recommendations(user, session):
    """Generate AI-powered health recommendations"""
    recommendations = []
    
    # Get user's recent data
    recent_symptoms = crud.get_user_symptoms(session, user.id, days=7)
    recent_meals = crud.get_user_meals(session, user.id, days=7)
    
    # BMI-based recommendations
    height_m = user.height_cm / 100
    bmi = user.weight_kg / (height_m * height_m)
    
    if bmi < 18.5:
        recommendations.append("Your BMI suggests you may be underweight. Consider increasing your calorie intake with nutrient-rich foods.")
    elif bmi > 25:
        recommendations.append("Your BMI suggests you may be overweight. Focus on portion control and regular exercise.")
    
    # Allergy-based recommendations
    if user.allergies:
        recommendations.append(f"Remember to avoid foods containing: {', '.join(user.allergies)}")
    
    # Symptom-based recommendations
    if recent_symptoms:
        food_intolerance_count = len([s for s in recent_symptoms if s.ai_classification == "food-intolerance"])
        if food_intolerance_count > 2:
            recommendations.append("You've experienced several food intolerance symptoms. Consider keeping a detailed food diary to identify triggers.")
    
    # Meal pattern recommendations
    if recent_meals:
        meal_count = len(recent_meals)
        if meal_count < 14:  # Less than 2 meals per day on average
            recommendations.append("You may not be eating enough meals. Try to eat 3-4 balanced meals per day.")
    
    # Disease-specific recommendations
    if user.diseases:
        if "diabetes" in [d.lower() for d in user.diseases]:
            recommendations.append("Monitor your carbohydrate intake and blood sugar levels regularly.")
        if "hypertension" in [d.lower() for d in user.diseases]:
            recommendations.append("Limit sodium intake and focus on potassium-rich foods like bananas and spinach.")
    
    return recommendations

@app.post("/progress/log")
def log_progress(progress: schemas.ProgressCreate, session: Session = Depends(get_db)):
    """Log health progress metrics"""
    user = crud.get_user(session, progress.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = crud.create_progress(session, progress)
    return {"message": "Progress logged successfully", "id": result.id}

@app.get("/progress/{user_id}")
def get_progress(user_id: str, days: int = 30, session: Session = Depends(get_db)):
    """Get user's progress history"""
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud.get_user_progress(session, user_id, days)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "HealthSync API"}
