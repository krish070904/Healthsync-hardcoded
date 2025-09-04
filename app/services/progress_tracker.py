from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..models.progress import Progress

class ProgressTracker:
    """
    Service for tracking and analyzing user health progress over time.
    Provides functionality for trend analysis, goal tracking, and health insights.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_progress(self, progress_data: schemas.ProgressCreate) -> Progress:
        """
        Log a new progress entry for a user
        """
        return crud.create_progress(self.db, progress_data)
    
    def get_progress_history(self, user_id: str, days: int = 30) -> List[Progress]:
        """
        Get a user's progress history for the specified time period
        """
        return crud.get_user_progress(self.db, user_id, days)
    
    def analyze_weight_trend(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze weight trends over time and provide insights
        """
        progress_history = self.get_progress_history(user_id, days)
        
        if not progress_history or len(progress_history) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least two weight measurements to analyze trends"
            }
        
        # Extract weight data points with timestamps
        weight_data = [(p.timestamp, p.weight_kg) for p in progress_history if p.weight_kg is not None]
        weight_data.sort(key=lambda x: x[0])  # Sort by timestamp
        
        if len(weight_data) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least two weight measurements to analyze trends"
            }
        
        # Calculate overall change
        first_weight = weight_data[0][1]
        last_weight = weight_data[-1][1]
        total_change = last_weight - first_weight
        percent_change = (total_change / first_weight) * 100
        
        # Calculate rate of change (per week)
        days_elapsed = (weight_data[-1][0] - weight_data[0][0]).days
        if days_elapsed < 1:
            days_elapsed = 1  # Avoid division by zero
        
        weekly_change_rate = (total_change / days_elapsed) * 7
        
        # Determine trend direction
        if abs(total_change) < 0.5:  # Less than 0.5 kg change
            trend = "stable"
        elif total_change > 0:
            trend = "gaining"
        else:
            trend = "losing"
        
        # Generate health insights based on trend
        insights = self._generate_weight_insights(trend, weekly_change_rate, total_change)
        
        return {
            "status": "success",
            "first_measurement": {
                "date": weight_data[0][0].isoformat(),
                "weight_kg": weight_data[0][1]
            },
            "latest_measurement": {
                "date": weight_data[-1][0].isoformat(),
                "weight_kg": weight_data[-1][1]
            },
            "total_change_kg": round(total_change, 2),
            "percent_change": round(percent_change, 2),
            "weekly_change_rate_kg": round(weekly_change_rate, 2),
            "trend": trend,
            "data_points": len(weight_data),
            "days_tracked": days_elapsed,
            "insights": insights
        }
    
    def _generate_weight_insights(self, trend: str, weekly_change_rate: float, total_change: float) -> List[str]:
        """
        Generate health insights based on weight trends
        """
        insights = []
        
        if trend == "stable":
            insights.append("Your weight has remained stable over this period.")
        elif trend == "gaining":
            insights.append(f"You've gained {abs(round(total_change, 2))} kg over this period.")
            
            if weekly_change_rate > 0.9:  # More than 0.9 kg per week
                insights.append("Your rate of weight gain is relatively fast. Consider reviewing your diet and exercise routine.")
        elif trend == "losing":
            insights.append(f"You've lost {abs(round(total_change, 2))} kg over this period.")
            
            if weekly_change_rate < -1.0:  # Losing more than 1 kg per week
                insights.append("You're losing weight at a rapid pace. While weight loss may be your goal, losing too quickly can sometimes be unhealthy.")
            elif weekly_change_rate > -0.5 and weekly_change_rate < 0:  # Slow, steady loss
                insights.append("You're losing weight at a healthy, sustainable pace. Great job!")
        
        return insights
    
    def analyze_blood_pressure_trend(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze blood pressure trends over time and provide insights
        """
        progress_history = self.get_progress_history(user_id, days)
        
        if not progress_history:
            return {
                "status": "insufficient_data",
                "message": "No blood pressure measurements found"
            }
        
        # Extract blood pressure data points with timestamps
        bp_data = [
            (p.timestamp, p.blood_pressure_systolic, p.blood_pressure_diastolic) 
            for p in progress_history 
            if p.blood_pressure_systolic is not None and p.blood_pressure_diastolic is not None
        ]
        
        if not bp_data:
            return {
                "status": "insufficient_data",
                "message": "No blood pressure measurements found"
            }
        
        bp_data.sort(key=lambda x: x[0])  # Sort by timestamp
        
        # Calculate averages and ranges
        systolic_values = [bp[1] for bp in bp_data]
        diastolic_values = [bp[2] for bp in bp_data]
        
        avg_systolic = sum(systolic_values) / len(systolic_values)
        avg_diastolic = sum(diastolic_values) / len(diastolic_values)
        
        # Categorize blood pressure based on average
        category = self._categorize_blood_pressure(avg_systolic, avg_diastolic)
        
        # Generate insights
        insights = self._generate_blood_pressure_insights(category, avg_systolic, avg_diastolic)
        
        return {
            "status": "success",
            "average_systolic": round(avg_systolic, 1),
            "average_diastolic": round(avg_diastolic, 1),
            "min_systolic": min(systolic_values),
            "max_systolic": max(systolic_values),
            "min_diastolic": min(diastolic_values),
            "max_diastolic": max(diastolic_values),
            "category": category,
            "data_points": len(bp_data),
            "insights": insights
        }
    
    def _categorize_blood_pressure(self, systolic: float, diastolic: float) -> str:
        """
        Categorize blood pressure according to standard guidelines
        """
        if systolic < 120 and diastolic < 80:
            return "normal"
        elif (120 <= systolic < 130) and diastolic < 80:
            return "elevated"
        elif (130 <= systolic < 140) or (80 <= diastolic < 90):
            return "hypertension_stage_1"
        elif (systolic >= 140) or (diastolic >= 90):
            return "hypertension_stage_2"
        elif systolic > 180 or diastolic > 120:
            return "hypertensive_crisis"
        else:
            return "unknown"
    
    def _generate_blood_pressure_insights(self, category: str, systolic: float, diastolic: float) -> List[str]:
        """
        Generate health insights based on blood pressure category
        """
        insights = []
        
        if category == "normal":
            insights.append("Your blood pressure is in the normal range. Keep up the good work!")
        elif category == "elevated":
            insights.append("Your blood pressure is slightly elevated. Consider lifestyle changes like reducing sodium intake and increasing physical activity.")
        elif category == "hypertension_stage_1":
            insights.append("Your blood pressure falls into hypertension stage 1. Consider consulting with a healthcare provider about lifestyle changes and possibly medication.")
        elif category == "hypertension_stage_2":
            insights.append("Your blood pressure falls into hypertension stage 2. It's recommended to consult with a healthcare provider about a treatment plan.")
        elif category == "hypertensive_crisis":
            insights.append("Your blood pressure readings indicate a hypertensive crisis. If these readings are accurate, please seek immediate medical attention.")
        
        return insights
    
    def track_goal_progress(self, user_id: str, goal_type: str, target_value: float) -> Dict[str, Any]:
        """
        Track progress toward a specific health goal
        
        goal_type can be: 'weight', 'blood_sugar', 'blood_pressure', etc.
        """
        progress_history = self.get_progress_history(user_id, days=90)  # Get 90 days of history
        
        if not progress_history:
            return {
                "status": "insufficient_data",
                "message": "No progress data found"
            }
        
        # Get the latest value based on goal type
        latest_value = None
        if goal_type == "weight":
            latest_entries = [p for p in progress_history if p.weight_kg is not None]
            if latest_entries:
                latest_entries.sort(key=lambda x: x.timestamp, reverse=True)
                latest_value = latest_entries[0].weight_kg
        elif goal_type == "blood_sugar":
            latest_entries = [p for p in progress_history if p.blood_sugar is not None]
            if latest_entries:
                latest_entries.sort(key=lambda x: x.timestamp, reverse=True)
                latest_value = latest_entries[0].blood_sugar
        elif goal_type == "blood_pressure":
            latest_entries = [p for p in progress_history if p.blood_pressure_systolic is not None]
            if latest_entries:
                latest_entries.sort(key=lambda x: x.timestamp, reverse=True)
                latest_value = latest_entries[0].blood_pressure_systolic  # Using systolic as the tracked value
        
        if latest_value is None:
            return {
                "status": "insufficient_data",
                "message": f"No {goal_type} data found"
            }
        
        # Calculate progress percentage
        initial_entries = [p for p in progress_history if getattr(p, self._get_attribute_for_goal(goal_type)) is not None]
        if not initial_entries:
            return {
                "status": "insufficient_data",
                "message": f"No initial {goal_type} data found"
            }
        
        initial_entries.sort(key=lambda x: x.timestamp)
        initial_value = getattr(initial_entries[0], self._get_attribute_for_goal(goal_type))
        
        # Calculate progress toward goal
        if goal_type == "weight":
            # For weight, we might be trying to lose or gain
            if target_value < initial_value:  # Weight loss goal
                total_change_needed = initial_value - target_value
                current_change = initial_value - latest_value
            else:  # Weight gain goal
                total_change_needed = target_value - initial_value
                current_change = latest_value - initial_value
        else:
            # For other metrics, assume we're trying to reach a specific target
            total_change_needed = abs(target_value - initial_value)
            current_change = abs(latest_value - initial_value)
        
        if total_change_needed == 0:  # Already at goal
            progress_percentage = 100
        else:
            progress_percentage = min(100, (current_change / total_change_needed) * 100)
        
        # Generate insights
        insights = []
        if progress_percentage >= 100:
            insights.append(f"Congratulations! You've reached your {goal_type} goal.")
        elif progress_percentage >= 75:
            insights.append(f"You're making excellent progress toward your {goal_type} goal. Keep it up!")
        elif progress_percentage >= 50:
            insights.append(f"You're halfway to your {goal_type} goal. Stay consistent!")
        elif progress_percentage >= 25:
            insights.append(f"You're making steady progress toward your {goal_type} goal.")
        elif progress_percentage > 0:
            insights.append(f"You've started making progress toward your {goal_type} goal.")
        else:
            insights.append(f"You haven't made progress toward your {goal_type} goal yet. Consider reviewing your approach.")
        
        return {
            "status": "success",
            "goal_type": goal_type,
            "target_value": target_value,
            "initial_value": initial_value,
            "current_value": latest_value,
            "progress_percentage": round(progress_percentage, 1),
            "insights": insights
        }
    
    def _get_attribute_for_goal(self, goal_type: str) -> str:
        """
        Map goal type to the corresponding model attribute
        """
        mapping = {
            "weight": "weight_kg",
            "blood_sugar": "blood_sugar",
            "blood_pressure": "blood_pressure_systolic"
        }
        return mapping.get(goal_type, goal_type)
    
    def generate_health_report(self, user_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive health report with insights across all tracked metrics
        """
        # Get user data
        user = crud.get_user(self.db, user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get progress history
        progress_history = self.get_progress_history(user_id, days=90)
        
        # Get meal logs
        meal_logs = crud.get_user_meals(self.db, user_id, days=30)
        
        # Get symptom logs
        symptom_logs = crud.get_user_symptoms(self.db, user_id, days=30)
        
        # Analyze weight trends
        weight_analysis = self.analyze_weight_trend(user_id, days=90)
        
        # Analyze blood pressure trends
        bp_analysis = self.analyze_blood_pressure_trend(user_id, days=90)
        
        # Compile report
        report = {
            "status": "success",
            "user_id": user_id,
            "report_date": datetime.utcnow().isoformat(),
            "user_info": {
                "name": user.name,
                "age": self._calculate_age(user.dob) if user.dob else None,
                "gender": user.gender,
                "height_cm": user.height_cm,
                "current_weight_kg": self._get_latest_weight(progress_history)
            },
            "summary": {
                "data_points_collected": len(progress_history) + len(meal_logs) + len(symptom_logs),
                "days_tracked": 90,
                "metrics_tracked": self._get_tracked_metrics(progress_history)
            },
            "weight_analysis": weight_analysis if weight_analysis.get("status") == "success" else None,
            "blood_pressure_analysis": bp_analysis if bp_analysis.get("status") == "success" else None,
            "nutrition_summary": self._summarize_nutrition(meal_logs),
            "symptom_patterns": self._analyze_symptom_patterns(symptom_logs),
            "recommendations": self._generate_recommendations(user, progress_history, meal_logs, symptom_logs)
        }
        
        return report
    
    def _calculate_age(self, dob_str: str) -> Optional[int]:
        """
        Calculate age from date of birth string
        """
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.utcnow()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except:
            return None
    
    def _get_latest_weight(self, progress_history: List[Progress]) -> Optional[float]:
        """
        Get the latest weight measurement from progress history
        """
        weight_entries = [p for p in progress_history if p.weight_kg is not None]
        if not weight_entries:
            return None
        
        weight_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return weight_entries[0].weight_kg
    
    def _get_tracked_metrics(self, progress_history: List[Progress]) -> List[str]:
        """
        Determine which metrics are being tracked based on progress history
        """
        metrics = []
        
        if any(p.weight_kg is not None for p in progress_history):
            metrics.append("weight")
        
        if any(p.blood_sugar is not None for p in progress_history):
            metrics.append("blood_sugar")
        
        if any(p.blood_pressure_systolic is not None for p in progress_history):
            metrics.append("blood_pressure")
        
        return metrics
    
    def _summarize_nutrition(self, meal_logs: List[Any]) -> Dict[str, Any]:
        """
        Summarize nutrition data from meal logs
        """
        if not meal_logs:
            return {"status": "insufficient_data"}
        
        # Calculate average daily calories
        daily_calories = {}
        for meal in meal_logs:
            date_str = meal.timestamp.date().isoformat()
            if date_str not in daily_calories:
                daily_calories[date_str] = 0
            daily_calories[date_str] += meal.total_calories
        
        avg_daily_calories = sum(daily_calories.values()) / len(daily_calories)
        
        # Count meal types
        meal_types = {}
        for meal in meal_logs:
            meal_type = meal.meal_type.lower()
            if meal_type not in meal_types:
                meal_types[meal_type] = 0
            meal_types[meal_type] += 1
        
        return {
            "status": "success",
            "average_daily_calories": round(avg_daily_calories, 1),
            "days_tracked": len(daily_calories),
            "meal_frequency": meal_types,
            "insights": self._generate_nutrition_insights(avg_daily_calories, meal_types)
        }
    
    def _generate_nutrition_insights(self, avg_daily_calories: float, meal_types: Dict[str, int]) -> List[str]:
        """
        Generate insights based on nutrition data
        """
        insights = []
        
        # Calorie insights
        if avg_daily_calories < 1200:
            insights.append("Your average calorie intake appears to be quite low. Ensure you're getting adequate nutrition.")
        elif avg_daily_calories > 2500:
            insights.append("Your average calorie intake is relatively high. Consider reviewing portion sizes if weight management is a goal.")
        
        # Meal frequency insights
        total_meals = sum(meal_types.values())
        days = total_meals / 3  # Approximate number of days based on 3 meals per day
        
        breakfast_count = meal_types.get("breakfast", 0)
        if breakfast_count / days < 0.7 and days >= 3:  # Less than 70% of days have breakfast
            insights.append("You appear to skip breakfast frequently. Consider adding a nutritious breakfast to start your day.")
        
        if "snack" in meal_types and meal_types["snack"] > days * 2:  # More than 2 snacks per day on average
            insights.append("You log frequent snacks. Consider the nutritional content of snacks and whether they're supporting your health goals.")
        
        return insights
    
    def _analyze_symptom_patterns(self, symptom_logs: List[Any]) -> Dict[str, Any]:
        """
        Analyze patterns in symptom logs
        """
        if not symptom_logs:
            return {"status": "insufficient_data"}
        
        # Count symptom occurrences
        symptom_counts = {}
        severity_by_symptom = {}
        for log in symptom_logs:
            for symptom in log.symptoms:
                if symptom not in symptom_counts:
                    symptom_counts[symptom] = 0
                    severity_by_symptom[symptom] = []
                symptom_counts[symptom] += 1
                severity_by_symptom[symptom].append(log.severity)
        
        # Calculate average severity for each symptom
        avg_severity = {}
        for symptom, severities in severity_by_symptom.items():
            avg_severity[symptom] = sum(severities) / len(severities)
        
        # Sort symptoms by frequency
        sorted_symptoms = sorted(
            symptom_counts.items(),
            key=lambda x: (x[1], avg_severity[x[0]]),
            reverse=True
        )
        
        # Generate insights
        insights = []
        if sorted_symptoms:
            most_common = sorted_symptoms[0][0]
            insights.append(
                f"Your most frequently reported symptom is '{most_common}' "
                f"with an average severity of {round(avg_severity[most_common], 1)}/10."
            )
        
        high_severity_symptoms = [
            s for s, sev in avg_severity.items()
            if sev >= 7 and symptom_counts[s] >= 2
        ]
        if high_severity_symptoms:
            insights.append(
                "The following symptoms consistently show high severity and may need attention: "
                f"{', '.join(high_severity_symptoms)}"
            )
        
        return {
            "status": "success",
            "total_logs": len(symptom_logs),
            "unique_symptoms": len(symptom_counts),
            "symptom_frequency": dict(sorted_symptoms[:5]),  # Top 5 most frequent
            "avg_severity": {s: round(sev, 1) for s, sev in avg_severity.items()},
            "insights": insights
        }
    
    def _generate_recommendations(self, user: Any, progress_history: List[Progress],
                                meal_logs: List[Any], symptom_logs: List[Any]) -> List[str]:
        """
        Generate personalized health recommendations based on all available data
        """
        recommendations = []
        
        # Weight-related recommendations
        if progress_history:
            weight_entries = [p for p in progress_history if p.weight_kg is not None]
            if weight_entries:
                weight_entries.sort(key=lambda x: x.timestamp)
                first_weight = weight_entries[0].weight_kg
                last_weight = weight_entries[-1].weight_kg
                weight_change = last_weight - first_weight
                
                if abs(weight_change) > 2:  # More than 2 kg change
                    if weight_change > 0:
                        recommendations.append(
                            "Consider consulting with a nutritionist about your recent weight gain "
                            "to ensure it aligns with your health goals."
                        )
                    else:
                        recommendations.append(
                            "Your recent weight loss might benefit from professional guidance "
                            "to ensure it's happening at a healthy rate."
                        )
        
        # Symptom-related recommendations
        if symptom_logs:
            high_severity_count = sum(1 for log in symptom_logs if log.severity >= 8)
            if high_severity_count >= 2:
                recommendations.append(
                    "You've reported multiple high-severity symptoms recently. "
                    "Consider scheduling a check-up with your healthcare provider."
                )
        
        # Nutrition-related recommendations
        if meal_logs:
            # Check meal timing patterns
            meal_times = {}
            for meal in meal_logs:
                hour = meal.timestamp.hour
                if meal.meal_type not in meal_times:
                    meal_times[meal.meal_type] = []
                meal_times[meal.meal_type].append(hour)
            
            # Look for late-night eating
            late_meals = sum(1 for meals in meal_times.values()
                           for hour in meals if hour >= 22)
            if late_meals >= 3:
                recommendations.append(
                    "Consider avoiding late-night meals as they might affect your sleep "
                    "quality and digestion."
                )
        
        # General health recommendations
        if not recommendations:
            recommendations.append(
                "Keep up with your current health tracking habits. Regular monitoring "
                "is key to maintaining and improving your health."
            )
        
        return recommendations