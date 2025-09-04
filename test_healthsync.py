#!/usr/bin/env python3
"""
HealthSync Demo Script
This script demonstrates the key features of the HealthSync AI health assistant.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def print_response(response, title):
    """Pretty print API responses"""
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print(f"{'='*50}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
    print(f"{'='*50}\n")

def test_healthsync():
    """Run comprehensive HealthSync demo"""
    
    print("🚀 HealthSync AI Health Assistant Demo")
    print("Starting comprehensive system test...\n")
    
    # 1. Check API health
    print("1️⃣ Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "API Health Check")
    
    # 2. Create a test user
    print("2️⃣ Creating test user...")
    user_data = {
        "name": "John Doe",
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 70,
        "allergies": ["peanut", "shellfish"],
        "diseases": ["diabetes"],
        "preferences": {"diet": "balanced", "cuisine": "mediterranean"}
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    print_response(response, "User Creation")
    
    if response.status_code != 200:
        print("❌ Failed to create user. Exiting demo.")
        return
    
    user_id = response.json()["id"]
    print(f"✅ User created with ID: {user_id}")
    
    # 3. Load sample food data
    print("3️⃣ Loading sample food data...")
    response = requests.post(f"{BASE_URL}/food/load_sample")
    print_response(response, "Food Data Loading")
    
    # 4. Generate personalized meal plan
    print("4️⃣ Generating personalized meal plan...")
    response = requests.get(f"{BASE_URL}/generate_plan/{user_id}")
    print_response(response, "Personalized Meal Plan")
    
    # 5. Log some symptoms
    print("5️⃣ Logging symptoms with AI classification...")
    symptoms_data = [
        {
            "user_id": user_id,
            "symptoms": ["nausea", "bloating"],
            "severity": 6
        },
        {
            "user_id": user_id,
            "symptoms": ["fever", "headache"],
            "severity": 8
        },
        {
            "user_id": user_id,
            "symptoms": ["fatigue", "mild headache"],
            "severity": 4
        }
    ]
    
    for i, symptom_data in enumerate(symptoms_data, 1):
        print(f"   Logging symptom set {i}...")
        response = requests.post(f"{BASE_URL}/symptoms/log", json=symptom_data)
        print_response(response, f"Symptom Log {i}")
        time.sleep(1)
    
    # 6. Log meals
    print("6️⃣ Logging meals...")
    meals_data = [
        {
            "user_id": user_id,
            "meal_type": "breakfast",
            "foods": [
                {"name": "Oats", "calories": 389, "grams": 100},
                {"name": "Milk (whole)", "calories": 61, "grams": 100}
            ],
            "symptoms_after": []
        },
        {
            "user_id": user_id,
            "meal_type": "lunch",
            "foods": [
                {"name": "Chicken breast", "calories": 165, "grams": 100},
                {"name": "Broccoli", "calories": 55, "grams": 91}
            ],
            "symptoms_after": ["bloating"]
        },
        {
            "user_id": user_id,
            "meal_type": "dinner",
            "foods": [
                {"name": "Brown rice", "calories": 111, "grams": 100},
                {"name": "Egg (boiled)", "calories": 155, "grams": 50}
            ],
            "symptoms_after": []
        }
    ]
    
    for i, meal_data in enumerate(meals_data, 1):
        print(f"   Logging meal {i}...")
        response = requests.post(f"{BASE_URL}/meals/log", json=meal_data)
        print_response(response, f"Meal Log {i}")
        time.sleep(1)
    
    # 7. Log progress metrics
    print("7️⃣ Logging health progress...")
    progress_data = [
        {
            "user_id": user_id,
            "weight_kg": 70.5,
            "blood_sugar": 120,
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "notes": "Feeling good today"
        },
        {
            "user_id": user_id,
            "weight_kg": 71.2,
            "blood_sugar": 145,
            "blood_pressure_systolic": 145,
            "blood_pressure_diastolic": 90,
            "notes": "Blood pressure slightly elevated"
        }
    ]
    
    for i, progress in enumerate(progress_data, 1):
        print(f"   Logging progress {i}...")
        response = requests.post(f"{BASE_URL}/progress/log", json=progress)
        print_response(response, f"Progress Log {i}")
        time.sleep(1)
    
    # 8. Get symptom analysis
    print("8️⃣ Getting AI symptom analysis...")
    response = requests.get(f"{BASE_URL}/symptoms/user/{user_id}/analysis")
    print_response(response, "AI Symptom Analysis")
    
    # 9. Get nutrition summary
    print("9️⃣ Getting nutrition summary...")
    response = requests.get(f"{BASE_URL}/meals/user/{user_id}/nutrition-summary")
    print_response(response, "Nutrition Summary")
    
    # 10. Get food-symptom correlations
    print("🔟 Analyzing food-symptom correlations...")
    response = requests.get(f"{BASE_URL}/meals/user/{user_id}/food-correlations")
    print_response(response, "Food-Symptom Correlations")
    
    # 11. Check health status and generate alerts
    print("1️⃣1️⃣ Checking health status and generating alerts...")
    response = requests.post(f"{BASE_URL}/alerts/user/{user_id}/check-health-status")
    print_response(response, "Health Status Check")
    
    # 12. Get alerts summary
    print("1️⃣2️⃣ Getting alerts summary...")
    response = requests.get(f"{BASE_URL}/alerts/user/{user_id}/summary")
    print_response(response, "Alerts Summary")
    
    # 13. Get user's alerts
    print("1️⃣3️⃣ Getting user's health alerts...")
    response = requests.get(f"{BASE_URL}/alerts/user/{user_id}")
    print_response(response, "User Health Alerts")
    
    # 14. Get progress history
    print("1️⃣4️⃣ Getting progress history...")
    response = requests.get(f"{BASE_URL}/progress/{user_id}")
    print_response(response, "Progress History")
    
    print("🎉 HealthSync Demo Completed Successfully!")
    print(f"📊 User ID: {user_id}")
    print(f"🌐 API Documentation: {BASE_URL}/docs")
    print(f"🔍 Interactive API Explorer: {BASE_URL}/redoc")

if __name__ == "__main__":
    try:
        test_healthsync()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to HealthSync API.")
        print("💡 Make sure the server is running with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        print("💡 Check that all services are running and the database is accessible.")
