"""HealthSync Consultation API Routes

This module provides API routes for health consultation services.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

import random
import re
import logging
from datetime import datetime
from .. import db, crud, schemas
from ..services.consultation import HealthConsultation

# Set up logging
logger = logging.getLogger(__name__)

# Define request and response models for chat
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

# Function to process health messages and generate responses
def process_health_message(message: str, user_data: Optional[Dict[str, Any]] = None, db: Session = None) -> str:
    """
    Process a health-related message and generate an appropriate response.
    
    Args:
        message: The user's message
        user_data: Optional user health data for personalized responses
        db: Database session for querying additional data
        
    Returns:
        A response string from the health assistant
    """
    # Convert message to lowercase for easier matching
    message = message.lower()
    
    # Define patterns for common health queries
    patterns = {
        'greeting': r'\b(hi|hello|hey|greetings)\b',
        'how_are_you': r'\b(how are you|how\'re you|how are you doing)\b',
        'symptom': r'\b(headache|pain|fever|cough|cold|flu|nausea|vomiting|diarrhea|constipation|rash|itch|sore|fatigue|tired|exhausted|dizzy|dizziness)\b',
        'diet': r'\b(diet|nutrition|food|eat|eating|meal|meals|healthy eating|balanced diet)\b',
        'exercise': r'\b(exercise|workout|fitness|training|cardio|strength|yoga|run|running|jog|jogging|walk|walking)\b',
        'sleep': r'\b(sleep|insomnia|rest|nap|tired|exhausted|fatigue|drowsy|drowsiness)\b',
        'stress': r'\b(stress|anxiety|anxious|worry|worried|tension|pressure|overwhelm|overwhelmed)\b',
        'medication': r'\b(medicine|medication|drug|pill|tablet|capsule|prescription|dose|dosage)\b',
        'doctor': r'\b(doctor|physician|specialist|appointment|clinic|hospital|medical|healthcare provider)\b',
        'thanks': r'\b(thanks|thank you|appreciate|grateful)\b',
        'goodbye': r'\b(bye|goodbye|see you|talk to you later|farewell)\b'
    }
    
    # Check for pattern matches
    matched_patterns = []
    for pattern_name, pattern in patterns.items():
        if re.search(pattern, message):
            matched_patterns.append(pattern_name)
    
    # Generate response based on matched patterns
    if 'greeting' in matched_patterns:
        greetings = [
            "Hello! I'm your HealthSync assistant. How can I help you today?",
            "Hi there! I'm here to help with your health questions. What can I assist you with?",
            "Greetings! I'm your health assistant. How may I help you today?"
        ]
        return random.choice(greetings)
    
    elif 'how_are_you' in matched_patterns:
        return "I'm functioning well, thank you for asking! How can I assist with your health today?"
    
    elif 'thanks' in matched_patterns:
        return "You're welcome! Is there anything else I can help you with?"
    
    elif 'goodbye' in matched_patterns:
        return "Goodbye! Remember to take care of your health. Feel free to chat anytime you have health questions."
    
    elif 'symptom' in matched_patterns:
        # Personalized response if user data is available
        if user_data and 'symptom_analysis' in user_data:
            return f"I notice you've had some health symptoms recently. Based on your history, I recommend tracking these symptoms carefully. Would you like me to analyze your current symptoms in more detail?"
        else:
            return "I understand you're experiencing some symptoms. It's important to track them regularly. Could you provide more details about what you're experiencing, including when it started and any potential triggers?"
    
    elif 'diet' in matched_patterns:
        # Personalized response if user data is available
        if user_data and 'nutrition_assessment' in user_data:
            nutrition = user_data['nutrition_assessment']
            if 'recommendations' in nutrition and nutrition['recommendations']:
                return f"Based on your recent meal logs, here's a nutrition tip: {random.choice(nutrition['recommendations'])}"
        
        return "A balanced diet is essential for good health. Try to include a variety of fruits, vegetables, whole grains, lean proteins, and healthy fats in your meals. Would you like specific nutrition recommendations?"
    
    elif 'exercise' in matched_patterns:
        exercise_tips = [
            "Regular physical activity is important for overall health. Aim for at least 150 minutes of moderate exercise per week.",
            "Exercise benefits include improved mood, better sleep, and reduced risk of chronic diseases. Even short walks can make a difference!",
            "Finding an exercise you enjoy makes it easier to stay consistent. Have you tried different types of physical activities to see what you prefer?"
        ]
        return random.choice(exercise_tips)
    
    elif 'sleep' in matched_patterns:
        sleep_tips = [
            "Good sleep is crucial for health. Aim for 7-9 hours of quality sleep each night.",
            "To improve sleep, try maintaining a regular sleep schedule and creating a relaxing bedtime routine.",
            "Poor sleep can affect your mood, energy levels, and immune function. Consider limiting screen time before bed for better sleep quality."
        ]
        return random.choice(sleep_tips)
    
    elif 'stress' in matched_patterns:
        stress_tips = [
            "Stress management is important for both mental and physical health. Deep breathing, meditation, and physical activity can help reduce stress.",
            "Chronic stress can impact your health in many ways. Consider activities that help you relax, such as yoga, reading, or spending time in nature.",
            "If you're feeling overwhelmed by stress, talking to a mental health professional can provide valuable support and coping strategies."
        ]
        return random.choice(stress_tips)
    
    elif 'medication' in matched_patterns:
        return "It's important to take medications as prescribed by your healthcare provider. If you have questions about your medications, it's best to consult with your doctor or pharmacist directly."
    
    elif 'doctor' in matched_patterns:
        return "Regular check-ups with healthcare providers are an important part of preventive care. Is there a specific medical concern you'd like to discuss?"
    
    else:
        # General responses for unmatched queries
        general_responses = [
            "I'm here to help with your health questions. Could you provide more details about your concern?",
            "As your health assistant, I can provide general health information and personalized insights based on your data. What specific health topic are you interested in?",
            "I can assist with questions about symptoms, diet, exercise, sleep, and stress management. How can I help you today?"
        ]
        return random.choice(general_responses)

router = APIRouter(
    prefix="/consultation",
    tags=["consultation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ChatResponse)
async def chat_with_health_assistant(message: ChatMessage, db: Session = Depends(get_db)):
    """
    Chat with the health assistant to get personalized health advice.
    """
    user_id = message.user_id
    user_data = None
    
    # If user_id is provided, fetch user health data for personalized responses
    if user_id:
        try:
            # Get user health data from the database
            user_data = await get_user_health_data(user_id, db)
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
    
    # Process the message and generate a response
    response = process_health_message(message.message, user_data, db)
    
    return ChatResponse(response=response)


@router.get("/summary", response_class=HTMLResponse)
async def get_health_summary(user_id: str = Query(...), db: Session = Depends(get_db)):
    """
    Get a summary of the user's health data for display in the chat interface.
    """
    try:
        # This would normally fetch real user data from the database
        # For now, we'll return mock data
        summary = f"""
        <div class="health-summary">
            <h3>Recent Health Summary</h3>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            <ul>
                <li><strong>Blood Pressure:</strong> 120/80 mmHg (Normal)</li>
                <li><strong>Heart Rate:</strong> 72 bpm (Normal)</li>
                <li><strong>Recent Symptoms:</strong> Mild headache (2 days ago)</li>
                <li><strong>Sleep Quality:</strong> Good (7.5 hours avg)</li>
            </ul>
        </div>
        """
        return HTMLResponse(content=summary)
    except Exception as e:
        logger.error(f"Error generating health summary: {e}")
        return HTMLResponse(content="<p>Unable to load health summary at this time.</p>")

async def get_user_health_data(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Fetch user health data for personalized chat responses.
    
    Args:
        user_id: The user's ID
        db: Database session
        
    Returns:
        Dictionary containing user health data
    """
    try:
        # Create a consultation service instance
        consultation_service = HealthConsultation(db)
        
        # Get comprehensive health data
        health_data = await consultation_service.get_comprehensive_consultation(user_id)
        
        # Get food-symptom correlations
        correlations = await consultation_service.get_food_symptom_correlations(user_id)
        
        # Combine the data
        user_data = {**health_data}
        user_data['correlations'] = correlations
        
        return user_data
    except Exception as e:
        logger.error(f"Error fetching health data for user {user_id}: {e}")
        # Return empty dict if there's an error
        return {}


def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@router.get("/user/{user_id}", response_model=Dict[str, Any])
def get_user_consultation(user_id: str, session: Session = Depends(get_db)):
    """Get a comprehensive health consultation for a user.
    
    This endpoint analyzes user data including progress metrics, symptoms, and meal logs
    to provide personalized health recommendations.
    
    Args:
        user_id: The ID of the user to generate consultation for
        session: Database session
        
    Returns:
        A dictionary containing consultation data and recommendations
    """
    consultation_service = HealthConsultation(session)
    consultation = consultation_service.get_user_consultation(user_id)
    
    if consultation.get('status') == 'error':
        raise HTTPException(status_code=404, detail=consultation.get('message', 'User not found'))
    
    return consultation

@router.get("/user/{user_id}/food-symptom-correlations", response_model=Dict[str, Any])
def get_food_symptom_correlations(user_id: str, session: Session = Depends(get_db)):
    """Analyze correlations between foods and symptoms for a user.
    
    This endpoint analyzes the user's meal and symptom logs to identify potential
    food triggers for reported symptoms.
    
    Args:
        user_id: The ID of the user to analyze
        session: Database session
        
    Returns:
        A dictionary with food-symptom correlation analysis
    """
    consultation_service = HealthConsultation(session)
    correlations = consultation_service.get_food_symptom_correlations(user_id)
    
    if correlations.get('status') == 'error':
        raise HTTPException(status_code=404, detail=correlations.get('message', 'User not found'))
    
    return correlations

@router.post("/", response_model=ChatResponse)
def chat_with_health_assistant(chat_message: ChatMessage, session: Session = Depends(get_db)):
    """Chat with the health assistant.
    
    This endpoint processes user messages and generates appropriate health-related responses.
    
    Args:
        chat_message: The user's message and optional user_id
        session: Database session
        
    Returns:
        A response from the health assistant
    """
    user_id = chat_message.user_id
    message = chat_message.message.lower()
    
    # Get user data if user_id is provided
    user_data = None
    if user_id:
        user = crud.get_user(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's health data
        consultation_service = HealthConsultation(session)
        user_data = consultation_service.get_user_consultation(user_id)
    
    # Process the message and generate a response
    response = process_health_message(message, user_data, session)
    
    return {"response": response}

@router.get("/summary", response_model=Dict[str, str])
def get_health_summary(session: Session = Depends(get_db)):
    """Get a summary of the user's health data.
    
    This endpoint provides a concise summary of the user's health status.
    
    Args:
        session: Database session
        
    Returns:
        A dictionary with health summary categories
    """
    # In a real implementation, this would extract the user_id from the token
    # For now, we'll return a mock summary
    return {
        "general_health": "Your overall health appears to be good based on recent data.",
        "recent_symptoms": "You've reported mild headaches and occasional fatigue in the past week.",
        "nutrition": "Your diet has been balanced with adequate protein intake.",
        "activity": "You've been meeting your exercise goals consistently."
    }

@router.get("/health-tips/{category}", response_model=List[Dict[str, Any]])
def get_health_tips(category: str):
    """Get general health tips by category.
    
    This endpoint provides general health tips and recommendations based on the
    specified category.
    
    Args:
        category: The category of health tips to retrieve (e.g., nutrition, exercise, sleep)
        
    Returns:
        A list of health tips for the specified category
    """
    # Define health tips by category
    health_tips = {
        "nutrition": [
            {
                "title": "Balanced Diet",
                "description": "Aim for a balanced diet with plenty of fruits, vegetables, lean proteins, and whole grains.",
                "importance": "high"
            },
            {
                "title": "Portion Control",
                "description": "Be mindful of portion sizes to avoid overeating. Use smaller plates and listen to your body's hunger cues.",
                "importance": "medium"
            },
            {
                "title": "Hydration",
                "description": "Drink plenty of water throughout the day. Aim for 8 glasses or about 2 liters daily.",
                "importance": "high"
            },
            {
                "title": "Limit Processed Foods",
                "description": "Reduce intake of processed foods, which often contain excess sodium, sugar, and unhealthy fats.",
                "importance": "medium"
            },
            {
                "title": "Mindful Eating",
                "description": "Eat slowly and without distractions to enjoy your food and recognize when you're full.",
                "importance": "medium"
            }
        ],
        "exercise": [
            {
                "title": "Regular Activity",
                "description": "Aim for at least 150 minutes of moderate-intensity exercise per week.",
                "importance": "high"
            },
            {
                "title": "Strength Training",
                "description": "Include strength training exercises at least twice a week to maintain muscle mass and bone density.",
                "importance": "medium"
            },
            {
                "title": "Flexibility",
                "description": "Incorporate stretching or yoga to improve flexibility and reduce injury risk.",
                "importance": "medium"
            },
            {
                "title": "Daily Movement",
                "description": "Even on rest days, try to incorporate movement like walking or light stretching.",
                "importance": "medium"
            },
            {
                "title": "Find Activities You Enjoy",
                "description": "Choose physical activities you enjoy to increase the likelihood of sticking with them.",
                "importance": "high"
            }
        ],
        "sleep": [
            {
                "title": "Consistent Schedule",
                "description": "Maintain a consistent sleep schedule, even on weekends.",
                "importance": "high"
            },
            {
                "title": "Sleep Environment",
                "description": "Create a cool, dark, and quiet sleep environment for optimal rest.",
                "importance": "medium"
            },
            {
                "title": "Limit Screen Time",
                "description": "Avoid screens for at least an hour before bedtime to improve sleep quality.",
                "importance": "medium"
            },
            {
                "title": "Adequate Duration",
                "description": "Aim for 7-9 hours of sleep per night for adults.",
                "importance": "high"
            },
            {
                "title": "Relaxation Techniques",
                "description": "Practice relaxation techniques like deep breathing or meditation before bed.",
                "importance": "medium"
            }
        ],
        "stress": [
            {
                "title": "Mindfulness Practice",
                "description": "Incorporate mindfulness or meditation into your daily routine to manage stress.",
                "importance": "high"
            },
            {
                "title": "Regular Breaks",
                "description": "Take short breaks throughout the day to reset and reduce stress buildup.",
                "importance": "medium"
            },
            {
                "title": "Physical Activity",
                "description": "Regular exercise helps reduce stress hormones and promotes relaxation.",
                "importance": "high"
            },
            {
                "title": "Social Connection",
                "description": "Maintain social connections and don't hesitate to seek support when needed.",
                "importance": "medium"
            },
            {
                "title": "Time Management",
                "description": "Prioritize tasks and set realistic goals to reduce feeling overwhelmed.",
                "importance": "medium"
            }
        ],
        "hydration": [
            {
                "title": "Daily Water Intake",
                "description": "Aim for 8 glasses (about 2 liters) of water daily, adjusting for activity level and climate.",
                "importance": "high"
            },
            {
                "title": "Hydration Signs",
                "description": "Monitor urine color - pale yellow indicates good hydration.",
                "importance": "medium"
            },
            {
                "title": "Hydration Sources",
                "description": "Remember that fruits, vegetables, and soups also contribute to hydration.",
                "importance": "medium"
            },
            {
                "title": "Exercise Hydration",
                "description": "Drink water before, during, and after exercise to maintain performance and recovery.",
                "importance": "high"
            },
            {
                "title": "Limit Dehydrating Beverages",
                "description": "Moderate consumption of caffeine and alcohol, which can contribute to dehydration.",
                "importance": "medium"
            }
        ]
    }
    
    # Return tips for the requested category or 404 if category not found
    if category.lower() in health_tips:
        return health_tips[category.lower()]
    else:
        raise HTTPException(status_code=404, detail=f"Health tips for category '{category}' not found")

@router.get("/health-consultation-html", response_model=Dict[str, Any])
def get_consultation_html_data(user_id: str, session: Session = Depends(get_db)):
    """Get consultation data formatted for HTML display.
    
    This endpoint provides consultation data in a format suitable for rendering
    in the frontend HTML template.
    
    Args:
        user_id: The ID of the user to generate consultation for
        session: Database session
        
    Returns:
        A dictionary containing formatted consultation data for HTML display
    """
    consultation_service = HealthConsultation(session)
    consultation = consultation_service.get_user_consultation(user_id)
    
    if consultation.get('status') == 'error':
        raise HTTPException(status_code=404, detail=consultation.get('message', 'User not found'))
    
    # Get food-symptom correlations
    correlations = consultation_service.get_food_symptom_correlations(user_id)
    
    # Format data for HTML display
    html_data = {
        "status": "success",
        "user_id": user_id,
        "consultation_date": consultation.get('consultation_date'),
        "sections": [
            {
                "title": "General Health Status",
                "content": self._format_general_health(consultation.get('general_health_status', {}))
            },
            {
                "title": "Vital Signs Assessment",
                "content": self._format_vital_signs(consultation.get('vital_signs_assessment', {}))
            },
            {
                "title": "Symptom Analysis",
                "content": self._format_symptom_analysis(consultation.get('symptom_analysis', {}))
            },
            {
                "title": "Nutrition Assessment",
                "content": self._format_nutrition_assessment(consultation.get('nutrition_assessment', {}))
            },
            {
                "title": "Food-Symptom Correlations",
                "content": self._format_correlations(correlations.get('correlations', []))
            },
            {
                "title": "Recommendations",
                "content": self._format_recommendations(consultation.get('recommendations', []))
            }
        ]
    }
    
    return html_data

def _format_general_health(general_health: Dict[str, Any]) -> List[Dict[str, str]]:
    """Format general health data for HTML display."""
    formatted = []
    
    if general_health.get('bmi'):
        formatted.append({
            "label": "BMI",
            "value": f"{general_health['bmi']} ({general_health.get('bmi_category', 'unknown').replace('_', ' ')})"
        })
    
    if general_health.get('weight_trend'):
        formatted.append({
            "label": "Weight Trend",
            "value": general_health['weight_trend'].capitalize()
        })
    
    if general_health.get('age'):
        formatted.append({
            "label": "Age",
            "value": str(general_health['age'])
        })
    
    return formatted

def _format_vital_signs(vital_signs: Dict[str, Any]) -> List[Dict[str, str]]:
    """Format vital signs data for HTML display."""
    formatted = []
    
    if vital_signs.get('status') == 'insufficient_data':
        formatted.append({
            "label": "Status",
            "value": "Insufficient data to assess vital signs"
        })
        return formatted
    
    bp = vital_signs.get('blood_pressure')
    if bp:
        formatted.append({
            "label": "Blood Pressure",
            "value": f"{bp['systolic']}/{bp['diastolic']} mmHg ({bp.get('category', 'unknown').replace('_', ' ')})"
        })
    
    bs = vital_signs.get('blood_sugar')
    if bs:
        formatted.append({
            "label": "Blood Sugar",
            "value": f"{bs['value']} mg/dL ({bs.get('category', 'unknown').replace('_', ' ')})"
        })
    
    if vital_signs.get('timestamp'):
        formatted.append({
            "label": "Last Measured",
            "value": vital_signs['timestamp']
        })
    
    return formatted

def _format_symptom_analysis(symptom_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format symptom analysis data for HTML display."""
    formatted = []
    
    if symptom_analysis.get('status') == 'no_symptoms':
        formatted.append({
            "type": "text",
            "content": "No symptoms reported"
        })
        return formatted
    
    # Most common symptoms
    if symptom_analysis.get('most_common'):
        common_symptoms = []
        for symptom, data in symptom_analysis['most_common']:
            common_symptoms.append(f"{symptom} ({data['count']} occurrences)")
        
        if common_symptoms:
            formatted.append({
                "type": "list",
                "title": "Most Common Symptoms",
                "items": common_symptoms
            })
    
    # Most severe symptoms
    if symptom_analysis.get('most_severe'):
        severe_symptoms = []
        for symptom, data in symptom_analysis['most_severe']:
            severe_symptoms.append(f"{symptom} (severity: {data['avg_severity']}/3)")
        
        if severe_symptoms:
            formatted.append({
                "type": "list",
                "title": "Most Severe Symptoms",
                "items": severe_symptoms
            })
    
    # Potential food correlations
    if symptom_analysis.get('potential_food_correlations'):
        correlations = []
        for corr in symptom_analysis['potential_food_correlations']:
            triggers = ", ".join([f"{t['food']} ({t['time_before_symptom']} hours before)" for t in corr['potential_triggers']])
            correlations.append(f"{corr['symptom']} ({corr['severity']}) potentially triggered by: {triggers}")
        
        if correlations:
            formatted.append({
                "type": "list",
                "title": "Potential Food Triggers",
                "items": correlations
            })
    
    return formatted

def _format_nutrition_assessment(nutrition: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format nutrition assessment data for HTML display."""
    formatted = []
    
    if nutrition.get('status') == 'insufficient_data':
        formatted.append({
            "type": "text",
            "content": "Insufficient data for nutrition assessment"
        })
        return formatted
    
    # Days analyzed
    if nutrition.get('days_analyzed'):
        formatted.append({
            "type": "text",
            "content": f"Analysis based on {nutrition['days_analyzed']} days of meal data"
        })
    
    # Average daily intake
    if nutrition.get('average_daily'):
        avg = nutrition['average_daily']
        daily_items = [
            f"Calories: {avg['calories']} kcal",
            f"Protein: {avg['protein']} g",
            f"Carbohydrates: {avg['carbs']} g",
            f"Fat: {avg['fat']} g",
            f"Fiber: {avg['fiber']} g"
        ]
        
        formatted.append({
            "type": "list",
            "title": "Average Daily Intake",
            "items": daily_items
        })
    
    # Macronutrient ratio
    if nutrition.get('macronutrient_ratio'):
        ratio = nutrition['macronutrient_ratio']
        formatted.append({
            "type": "text",
            "content": f"Macronutrient Ratio: {ratio['protein']}% protein, {ratio['carbs']}% carbs, {ratio['fat']}% fat"
        })
    
    return formatted

def _format_correlations(correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format food-symptom correlations for HTML display."""
    formatted = []
    
    if not correlations:
        formatted.append({
            "type": "text",
            "content": "No significant food-symptom correlations found"
        })
        return formatted
    
    correlation_items = []
    for corr in correlations:
        confidence_map = {
            'low': '⚪',
            'medium': '🟡',
            'high': '🔴'
        }
        
        confidence_indicator = confidence_map.get(corr['confidence'], '⚪')
        correlation_items.append(
            f"{confidence_indicator} {corr['food']} → {corr['symptom']} ({corr['correlation_percentage']}% correlation, {corr['occurrences']} occurrences)"
        )
    
    formatted.append({
        "type": "list",
        "title": "Food-Symptom Correlations",
        "items": correlation_items
    })
    
    return formatted

def _format_recommendations(recommendations: List[str]) -> List[Dict[str, Any]]:
    """Format recommendations for HTML display."""
    if not recommendations:
        return [{
            "type": "text",
            "content": "No specific recommendations available"
        }]
    
    return [{
        "type": "list",
        "title": "Personalized Recommendations",
        "items": recommendations
    }]