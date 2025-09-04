"""HealthSync Consultation Service

This module provides rule-based health consultation services based on user data,
including progress metrics, symptoms, and meal logs.
"""

import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..models.user import User
from ..models.progress import Progress
from ..models.symptom_log import SymptomLog
from ..models.meal_log import MealLog

class HealthConsultation:
    """Provides rule-based health consultation services."""
    
    def __init__(self, db: Session):
        """Initialize the consultation service with database session.
        
        Args:
            db: Database session for querying user data
        """
        self.db = db
        
        # Define health reference ranges
        self.reference_ranges = {
            'blood_pressure': {
                'normal': {'systolic': (90, 120), 'diastolic': (60, 80)},
                'elevated': {'systolic': (120, 129), 'diastolic': (60, 80)},
                'hypertension_stage_1': {'systolic': (130, 139), 'diastolic': (80, 89)},
                'hypertension_stage_2': {'systolic': (140, 180), 'diastolic': (90, 120)},
                'hypertensive_crisis': {'systolic': (180, 300), 'diastolic': (120, 200)}
            },
            'blood_sugar': {
                'fasting': {'normal': (70, 99), 'prediabetes': (100, 125), 'diabetes': (126, 400)},
                'post_meal': {'normal': (70, 140), 'prediabetes': (140, 199), 'diabetes': (200, 400)}
            },
            'bmi': {
                'underweight': (0, 18.5),
                'normal': (18.5, 24.9),
                'overweight': (25, 29.9),
                'obese': (30, 100)
            }
        }
        
        # Define symptom severity thresholds
        self.symptom_severity = {
            'mild': 1,
            'moderate': 2,
            'severe': 3
        }
        
        # Define common food-symptom correlations
        self.common_food_triggers = {
            'headache': ['chocolate', 'cheese', 'alcohol', 'caffeine', 'msg', 'aspartame'],
            'bloating': ['dairy', 'beans', 'carbonated', 'wheat', 'onions', 'garlic'],
            'nausea': ['spicy', 'fried', 'fatty', 'dairy'],
            'fatigue': ['sugar', 'refined carbs', 'alcohol', 'caffeine'],
            'joint pain': ['nightshades', 'gluten', 'dairy', 'sugar', 'alcohol'],
            'skin rash': ['dairy', 'gluten', 'eggs', 'nuts', 'shellfish']
        }
    
    def get_user_consultation(self, user_id: str) -> Dict[str, Any]:
        """Generate a comprehensive health consultation for a user.
        
        Args:
            user_id: The ID of the user to generate consultation for
            
        Returns:
            A dictionary containing consultation data and recommendations
        """
        # Get user data
        user = crud.get_user(self.db, user_id)
        if not user:
            return {
                'status': 'error',
                'message': 'User not found'
            }
        
        # Get recent progress data
        progress_data = crud.get_user_progress(self.db, user_id, limit=10)
        
        # Get recent symptoms
        recent_symptoms = crud.get_user_symptoms(self.db, user_id, limit=20)
        
        # Get recent meals
        recent_meals = crud.get_user_meals(self.db, user_id, limit=20)
        
        # Generate consultation
        consultation = {
            'status': 'success',
            'user_id': user_id,
            'consultation_date': datetime.datetime.now().isoformat(),
            'general_health_status': self._assess_general_health(user, progress_data),
            'vital_signs_assessment': self._assess_vital_signs(progress_data),
            'symptom_analysis': self._analyze_symptoms(recent_symptoms, recent_meals),
            'nutrition_assessment': self._assess_nutrition(recent_meals, user),
            'recommendations': self._generate_recommendations(user, progress_data, recent_symptoms, recent_meals)
        }
        
        return consultation
    
    def _assess_general_health(self, user: User, progress_data: List[Progress]) -> Dict[str, Any]:
        """Assess the general health status of a user based on their profile and progress data.
        
        Args:
            user: User model object
            progress_data: List of progress entries
            
        Returns:
            Dictionary with general health assessment
        """
        # Calculate BMI if weight and height are available
        bmi = None
        bmi_category = None
        
        if user.height_cm and user.weight_kg:
            height_m = user.height_cm / 100
            bmi = round(user.weight_kg / (height_m * height_m), 1)
            
            # Determine BMI category
            for category, (min_val, max_val) in self.reference_ranges['bmi'].items():
                if min_val <= bmi < max_val:
                    bmi_category = category
                    break
        
        # Check for weight change if we have progress data
        weight_trend = None
        if len(progress_data) >= 2:
            first_weight = progress_data[-1].weight_kg
            latest_weight = progress_data[0].weight_kg
            
            if first_weight and latest_weight:
                weight_diff = latest_weight - first_weight
                if abs(weight_diff) < 0.5:
                    weight_trend = 'stable'
                elif weight_diff > 0:
                    weight_trend = 'increasing'
                else:
                    weight_trend = 'decreasing'
        
        return {
            'bmi': bmi,
            'bmi_category': bmi_category,
            'weight_trend': weight_trend,
            'age': self._calculate_age(user.date_of_birth) if user.date_of_birth else None
        }
    
    def _assess_vital_signs(self, progress_data: List[Progress]) -> Dict[str, Any]:
        """Assess vital signs from progress data.
        
        Args:
            progress_data: List of progress entries
            
        Returns:
            Dictionary with vital signs assessment
        """
        if not progress_data:
            return {
                'status': 'insufficient_data',
                'message': 'Not enough progress data to assess vital signs'
            }
        
        # Get latest progress entry
        latest = progress_data[0]
        
        # Assess blood pressure if available
        bp_category = None
        if latest.blood_pressure_systolic and latest.blood_pressure_diastolic:
            systolic = latest.blood_pressure_systolic
            diastolic = latest.blood_pressure_diastolic
            
            # Determine blood pressure category
            for category, ranges in self.reference_ranges['blood_pressure'].items():
                sys_min, sys_max = ranges['systolic']
                dia_min, dia_max = ranges['diastolic']
                
                if (sys_min <= systolic < sys_max) and (dia_min <= diastolic < dia_max):
                    bp_category = category
                    break
            
            # If systolic and diastolic fall into different categories, use the more severe one
            if not bp_category:
                for category, ranges in self.reference_ranges['blood_pressure'].items():
                    sys_min, sys_max = ranges['systolic']
                    dia_min, dia_max = ranges['diastolic']
                    
                    if (sys_min <= systolic < sys_max) or (dia_min <= diastolic < dia_max):
                        bp_category = category
                        break
        
        # Assess blood sugar if available
        blood_sugar_category = None
        if latest.blood_sugar:
            # Assume fasting blood sugar for simplicity
            # In a real app, we would need to know if it's fasting or post-meal
            bs = latest.blood_sugar
            bs_type = 'fasting'  # Default assumption
            
            for category, (min_val, max_val) in self.reference_ranges['blood_sugar'][bs_type].items():
                if min_val <= bs < max_val:
                    blood_sugar_category = category
                    break
        
        return {
            'blood_pressure': {
                'systolic': latest.blood_pressure_systolic,
                'diastolic': latest.blood_pressure_diastolic,
                'category': bp_category
            } if latest.blood_pressure_systolic and latest.blood_pressure_diastolic else None,
            'blood_sugar': {
                'value': latest.blood_sugar,
                'category': blood_sugar_category,
                'assumed_type': 'fasting'  # Note the assumption
            } if latest.blood_sugar else None,
            'timestamp': latest.timestamp.isoformat() if latest.timestamp else None
        }
    
    def _analyze_symptoms(self, symptom_logs: List[SymptomLog], meal_logs: List[MealLog]) -> Dict[str, Any]:
        """Analyze symptoms and potential correlations with meals.
        
        Args:
            symptoms: List of symptom logs
            meals: List of meal logs
            
        Returns:
            Dictionary with symptom analysis
        """
        if not symptoms:
            return {
                'status': 'no_symptoms',
                'message': 'No symptoms reported'
            }
        
        # Count symptom occurrences
        symptom_counts = {}
        for log in symptom_logs:
            symptom = {'name': log.symptom, 'severity': log.severity}
            if symptom['name'] not in symptom_counts:
                symptom_counts[symptom['name']] = {
                    'count': 0,
                    'severity_sum': 0,
                    'instances': []
                }
            
            symptom_counts[symptom['name']]['count'] += 1
            symptom_counts[symptom['name']]['severity_sum'] += self.symptom_severity.get(symptom['severity'], 1)
            symptom_counts[symptom['name']]['instances'].append({
                'timestamp': log.timestamp.isoformat(),
                'severity': symptom['severity']
            })
        
        # Calculate average severity
        for symptom, data in symptom_counts.items():
            data['avg_severity'] = round(data['severity_sum'] / data['count'], 1)
        
        # Find potential food correlations
        correlations = []
        if meals and symptoms:
            # For each symptom occurrence, look for meals within 24 hours before
            for log in symptoms:
                symptom_time = log.timestamp
                for symptom in log.symptoms:
                    symptom_name = symptom['name']
                    
                    # Look for meals within 24 hours before the symptom
                    potential_triggers = []
                    for meal in meals:
                        if meal.timestamp < symptom_time and (symptom_time - meal.timestamp).total_seconds() <= 86400:  # 24 hours
                            for item in meal.food_items:
                                # Check if this food is a common trigger for this symptom
                                for trigger_food in self.common_food_triggers.get(symptom_name.lower(), []):
                                    if trigger_food.lower() in item['name'].lower():
                                        potential_triggers.append({
                                            'food': item['name'],
                                            'time_before_symptom': round((symptom_time - meal.timestamp).total_seconds() / 3600, 1)  # hours
                                        })
                    
                    if potential_triggers:
                        correlations.append({
                            'symptom': symptom_name,
                            'severity': symptom['severity'],
                            'timestamp': symptom_time.isoformat(),
                            'potential_triggers': potential_triggers
                        })
        
        return {
            'most_common': sorted(symptom_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5],
            'most_severe': sorted(symptom_counts.items(), key=lambda x: x[1]['avg_severity'], reverse=True)[:5],
            'potential_food_correlations': correlations
        }
    
    def _assess_nutrition(self, meals: List[MealLog], user: User) -> Dict[str, Any]:
        """Assess nutrition based on meal logs.
        
        Args:
            meals: List of meal logs
            user: User model object
            
        Returns:
            Dictionary with nutrition assessment
        """
        if not meals:
            return {
                'status': 'insufficient_data',
                'message': 'Not enough meal data for nutrition assessment'
            }
        
        # Calculate daily averages
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        
        # Group meals by date
        meals_by_date = {}
        for meal in meals:
            date_str = meal.timestamp.date().isoformat()
            if date_str not in meals_by_date:
                meals_by_date[date_str] = []
            meals_by_date[date_str].append(meal)
        
        # Calculate daily totals
        daily_totals = {}
        for date, day_meals in meals_by_date.items():
            daily_totals[date] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0
            }
            
            for meal in day_meals:
                for item in meal.food_items:
                    daily_totals[date]['calories'] += item.get('calories', 0) or 0
                    daily_totals[date]['protein'] += item.get('protein_g', 0) or 0
                    daily_totals[date]['carbs'] += item.get('carbs_g', 0) or 0
                    daily_totals[date]['fat'] += item.get('fat_g', 0) or 0
                    daily_totals[date]['fiber'] += item.get('fiber_g', 0) or 0
        
        # Calculate averages
        num_days = len(daily_totals)
        avg_calories = sum(day['calories'] for day in daily_totals.values()) / num_days if num_days > 0 else 0
        avg_protein = sum(day['protein'] for day in daily_totals.values()) / num_days if num_days > 0 else 0
        avg_carbs = sum(day['carbs'] for day in daily_totals.values()) / num_days if num_days > 0 else 0
        avg_fat = sum(day['fat'] for day in daily_totals.values()) / num_days if num_days > 0 else 0
        avg_fiber = sum(day['fiber'] for day in daily_totals.values()) / num_days if num_days > 0 else 0
        
        # Calculate recommended values
        recommended_calories = self._calculate_recommended_calories(user)
        recommended_protein = user.weight_kg * 0.8  # 0.8g per kg of body weight
        recommended_fiber = 25  # general recommendation
        
        # Calculate macronutrient percentages
        total_macros = avg_protein * 4 + avg_carbs * 4 + avg_fat * 9  # calories from macros
        protein_pct = (avg_protein * 4 / total_macros * 100) if total_macros > 0 else 0
        carbs_pct = (avg_carbs * 4 / total_macros * 100) if total_macros > 0 else 0
        fat_pct = (avg_fat * 9 / total_macros * 100) if total_macros > 0 else 0
        
        return {
            'status': 'success',
            'days_analyzed': num_days,
            'average_daily': {
                'calories': round(avg_calories, 1),
                'protein': round(avg_protein, 1),
                'carbs': round(avg_carbs, 1),
                'fat': round(avg_fat, 1),
                'fiber': round(avg_fiber, 1)
            },
            'macronutrient_ratio': {
                'protein': round(protein_pct, 1),
                'carbs': round(carbs_pct, 1),
                'fat': round(fat_pct, 1)
            },
            'compared_to_recommended': {
                'calories': round((avg_calories / recommended_calories * 100) if recommended_calories else 0, 1),
                'protein': round((avg_protein / recommended_protein * 100) if recommended_protein else 0, 1),
                'fiber': round((avg_fiber / recommended_fiber * 100) if recommended_fiber else 0, 1)
            },
            'recommendations': self._generate_nutrition_recommendations(
                avg_calories, recommended_calories,
                protein_pct, carbs_pct, fat_pct,
                avg_fiber, recommended_fiber
            )
        }
    
    def _generate_recommendations(self, user: User, progress_data: List[Progress], 
                                 symptoms: List[SymptomLog], meals: List[MealLog]) -> List[str]:
        """Generate health recommendations based on all available data.
        
        Args:
            user: User model object
            progress_data: List of progress entries
            symptoms: List of symptom logs
            meals: List of meal logs
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Get latest progress if available
        latest_progress = progress_data[0] if progress_data else None
        
        # BMI-based recommendations
        if user.height_cm and user.weight_kg:
            height_m = user.height_cm / 100
            bmi = user.weight_kg / (height_m * height_m)
            
            if bmi < 18.5:
                recommendations.append("Your BMI indicates you're underweight. Consider increasing your caloric intake with nutrient-dense foods.")
            elif 25 <= bmi < 30:
                recommendations.append("Your BMI indicates you're overweight. Consider a moderate calorie deficit and regular exercise.")
            elif bmi >= 30:
                recommendations.append("Your BMI indicates obesity. We recommend consulting with a healthcare provider for a personalized weight management plan.")
        
        # Blood pressure recommendations
        if latest_progress and latest_progress.blood_pressure_systolic and latest_progress.blood_pressure_diastolic:
            systolic = latest_progress.blood_pressure_systolic
            diastolic = latest_progress.blood_pressure_diastolic
            
            if systolic >= 130 or diastolic >= 80:
                recommendations.append("Your blood pressure is elevated. Consider reducing sodium intake, increasing physical activity, and managing stress.")
            if systolic >= 140 or diastolic >= 90:
                recommendations.append("Your blood pressure indicates hypertension stage 2. Please consult with a healthcare provider.")
        
        # Blood sugar recommendations
        if latest_progress and latest_progress.blood_sugar:
            bs = latest_progress.blood_sugar
            
            if bs >= 100:
                recommendations.append("Your blood sugar is elevated. Consider reducing refined carbohydrates and sugar in your diet.")
            if bs >= 126:
                recommendations.append("Your fasting blood sugar indicates potential diabetes. Please consult with a healthcare provider.")
        
        # Symptom-based recommendations
        if symptoms:
            # Check for frequent or severe symptoms
            symptom_counts = {}
            for log in symptoms:
                for symptom in log.symptoms:
                    name = symptom['name']
                    severity = symptom['severity']
                    
                    if name not in symptom_counts:
                        symptom_counts[name] = {'count': 0, 'severe_count': 0}
                    
                    symptom_counts[name]['count'] += 1
                    if severity == 'severe':
                        symptom_counts[name]['severe_count'] += 1
            
            for name, counts in symptom_counts.items():
                if counts['severe_count'] >= 2:
                    recommendations.append(f"You've reported severe {name} multiple times. Please consult with a healthcare provider.")
                elif counts['count'] >= 3:
                    recommendations.append(f"You've frequently reported {name}. Consider keeping a detailed symptom journal to identify triggers.")
        
        # Nutrition recommendations from nutrition assessment
        if meals:
            nutrition_assessment = self._assess_nutrition(meals, user)
            if nutrition_assessment['status'] == 'success':
                recommendations.extend(nutrition_assessment.get('recommendations', []))
        
        return recommendations
    
    def _generate_nutrition_recommendations(self, avg_calories: float, recommended_calories: float,
                                           protein_pct: float, carbs_pct: float, fat_pct: float,
                                           avg_fiber: float, recommended_fiber: float) -> List[str]:
        """Generate nutrition-specific recommendations.
        
        Args:
            avg_calories: Average daily calorie intake
            recommended_calories: Recommended daily calorie intake
            protein_pct: Protein percentage of total macronutrients
            carbs_pct: Carbohydrate percentage of total macronutrients
            fat_pct: Fat percentage of total macronutrients
            avg_fiber: Average daily fiber intake
            recommended_fiber: Recommended daily fiber intake
            
        Returns:
            List of nutrition recommendation strings
        """
        recommendations = []
        
        # Calorie recommendations
        if avg_calories < recommended_calories * 0.8:
            recommendations.append(f"Your average calorie intake ({round(avg_calories)} kcal) is significantly below your estimated needs ({round(recommended_calories)} kcal). Consider increasing your food intake for adequate energy.")
        elif avg_calories > recommended_calories * 1.2:
            recommendations.append(f"Your average calorie intake ({round(avg_calories)} kcal) is significantly above your estimated needs ({round(recommended_calories)} kcal). Consider moderating your portions for weight management.")
        
        # Macronutrient balance recommendations
        if protein_pct < 10:
            recommendations.append("Your protein intake is low. Consider incorporating more lean meats, fish, legumes, or plant-based protein sources.")
        elif protein_pct > 35:
            recommendations.append("Your protein intake is very high. Consider balancing your diet with more fruits, vegetables, and whole grains.")
        
        if carbs_pct < 40:
            recommendations.append("Your carbohydrate intake is low. Consider adding more whole grains, fruits, and starchy vegetables for energy.")
        elif carbs_pct > 65:
            recommendations.append("Your carbohydrate intake is high. Consider focusing on complex carbs like whole grains and reducing simple sugars.")
        
        if fat_pct < 20:
            recommendations.append("Your fat intake is low. Consider adding healthy fats like avocados, nuts, seeds, and olive oil.")
        elif fat_pct > 35:
            recommendations.append("Your fat intake is high. Consider reducing saturated fats and focusing on healthier fat sources.")
        
        # Fiber recommendations
        if avg_fiber < recommended_fiber * 0.7:
            recommendations.append(f"Your fiber intake ({round(avg_fiber)} g) is below recommendations. Increase fruits, vegetables, legumes, and whole grains.")
        
        return recommendations
    
    def _calculate_recommended_calories(self, user: User) -> float:
        """Calculate recommended daily calorie intake based on user data.
        
        Args:
            user: User model object
            
        Returns:
            Recommended daily calorie intake
        """
        if not (user.height_cm and user.weight_kg and user.gender and user.date_of_birth):
            return 2000  # Default if missing data
        
        age = self._calculate_age(user.date_of_birth)
        if not age:
            return 2000  # Default if can't calculate age
        
        # Mifflin-St Jeor Equation
        height_cm = user.height_cm
        weight_kg = user.weight_kg
        gender = user.gender.lower()
        
        if gender in ('male', 'm'):
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:  # female
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        
        # Activity factor (default to lightly active)
        activity_factor = 1.375  # Lightly active
        
        return bmr * activity_factor
    
    def _calculate_age(self, date_of_birth: datetime.date) -> Optional[int]:
        """Calculate age from date of birth.
        
        Args:
            date_of_birth: Date of birth
            
        Returns:
            Age in years or None if date_of_birth is None
        """
        if not date_of_birth:
            return None
        
        today = datetime.date.today()
        age = today.year - date_of_birth.year
        
        # Adjust age if birthday hasn't occurred yet this year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        
        return age
    
    def get_food_symptom_correlations(self, user_id: str) -> Dict[str, Any]:
        """Analyze correlations between foods and symptoms.
        
        Args:
            user_id: The ID of the user to analyze
            
        Returns:
            Dictionary with food-symptom correlation analysis
        """
        # Get user data
        user = crud.get_user(self.db, user_id)
        if not user:
            return {
                'status': 'error',
                'message': 'User not found'
            }
        
        # Get symptoms and meals
        symptoms = crud.get_user_symptoms(self.db, user_id, limit=50)
        meals = crud.get_user_meals(self.db, user_id, limit=50)
        
        if not symptoms or not meals:
            return {
                'status': 'insufficient_data',
                'message': 'Not enough symptom or meal data for correlation analysis'
            }
        
        # Track food occurrences and symptom occurrences
        food_occurrences = {}
        symptom_occurrences = {}
        food_symptom_pairs = {}
        
        # Process meals
        for meal in meals:
            meal_date = meal.timestamp.date()
            for item in meal.food_items:
                food_name = item['name'].lower()
                if food_name not in food_occurrences:
                    food_occurrences[food_name] = 0
                food_occurrences[food_name] += 1
                
                # Check for symptoms within 24 hours after this meal
                for symptom_log in symptoms:
                    if symptom_log.timestamp.date() == meal_date or symptom_log.timestamp.date() == meal_date + datetime.timedelta(days=1):
                        # Check if symptom occurred after meal
                        if symptom_log.timestamp > meal.timestamp and (symptom_log.timestamp - meal.timestamp).total_seconds() <= 86400:  # 24 hours
                            for symptom in symptom_log.symptoms:
                                symptom_name = symptom['name'].lower()
                                
                                # Track symptom occurrence
                                if symptom_name not in symptom_occurrences:
                                    symptom_occurrences[symptom_name] = 0
                                symptom_occurrences[symptom_name] += 1
                                
                                # Track food-symptom pair
                                pair_key = f"{food_name}:{symptom_name}"
                                if pair_key not in food_symptom_pairs:
                                    food_symptom_pairs[pair_key] = {
                                        'food': food_name,
                                        'symptom': symptom_name,
                                        'count': 0,
                                        'time_to_symptom': []  # hours between food and symptom
                                    }
                                
                                food_symptom_pairs[pair_key]['count'] += 1
                                hours = (symptom_log.timestamp - meal.timestamp).total_seconds() / 3600
                                food_symptom_pairs[pair_key]['time_to_symptom'].append(round(hours, 1))
        
        # Calculate correlation scores
        correlations = []
        for pair_key, data in food_symptom_pairs.items():
            food = data['food']
            symptom = data['symptom']
            
            # Only consider pairs with multiple occurrences
            if data['count'] >= 2:
                # Calculate correlation score
                # Higher score means stronger correlation
                food_total = food_occurrences.get(food, 0)
                symptom_total = symptom_occurrences.get(symptom, 0)
                
                if food_total > 0 and symptom_total > 0:
                    # Calculate percentage of times symptom followed food
                    correlation_pct = (data['count'] / food_total) * 100
                    
                    # Calculate average time to symptom
                    avg_time = sum(data['time_to_symptom']) / len(data['time_to_symptom']) if data['time_to_symptom'] else 0
                    
                    correlations.append({
                        'food': food,
                        'symptom': symptom,
                        'occurrences': data['count'],
                        'correlation_percentage': round(correlation_pct, 1),
                        'average_time_to_symptom_hours': round(avg_time, 1),
                        'confidence': self._calculate_correlation_confidence(data['count'], food_total, symptom_total)
                    })
        
        # Sort by correlation percentage (highest first)
        correlations.sort(key=lambda x: x['correlation_percentage'], reverse=True)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'analysis_date': datetime.datetime.now().isoformat(),
            'data_points': {
                'meals_analyzed': len(meals),
                'symptoms_analyzed': len(symptoms),
                'unique_foods': len(food_occurrences),
                'unique_symptoms': len(symptom_occurrences)
            },
            'correlations': correlations[:10],  # Top 10 correlations
            'recommendations': self._generate_avoidance_recommendations(correlations)
        }
    
    def _calculate_correlation_confidence(self, pair_count: int, food_total: int, symptom_total: int) -> str:
        """Calculate confidence level for a food-symptom correlation.
        
        Args:
            pair_count: Number of times the food-symptom pair occurred
            food_total: Total occurrences of the food
            symptom_total: Total occurrences of the symptom
            
        Returns:
            Confidence level string (low, medium, high)
        """
        # Calculate confidence based on sample size and correlation strength
        if pair_count < 3:
            return 'low'
        
        correlation_pct = (pair_count / food_total) * 100
        
        if correlation_pct >= 75 and pair_count >= 5:
            return 'high'
        elif correlation_pct >= 50 and pair_count >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_avoidance_recommendations(self, correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate food avoidance recommendations based on correlations.
        
        Args:
            correlations: List of food-symptom correlations
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Only recommend avoiding foods with medium or high confidence
        for corr in correlations:
            if corr['confidence'] in ['medium', 'high'] and corr['correlation_percentage'] >= 50:
                food = corr['food']
                symptom = corr['symptom']
                pct = corr['correlation_percentage']
                
                if corr['confidence'] == 'high':
                    recommendations.append(f"Consider avoiding {food} as it strongly correlates with {symptom} ({pct}% of the time).")
                else:  # medium
                    recommendations.append(f"Consider temporarily eliminating {food} to see if {symptom} improves (correlation: {pct}%).")
        
        # Add general recommendation if we have specific ones
        if recommendations:
            recommendations.append("Try an elimination diet by removing suspected trigger foods for 2-4 weeks, then reintroducing them one at a time to confirm correlations.")
        
        return recommendations