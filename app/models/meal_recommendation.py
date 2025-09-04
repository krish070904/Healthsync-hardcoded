from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, ForeignKey, Boolean
from datetime import datetime
from ..db import Base
import uuid

def new_id():
    return str(uuid.uuid4())

class MealRecommendation(Base):
    """
    Model for storing meal recommendations history for each user.
    This allows tracking of recommendations over time and enables
    reinforcement learning for personalized meal planning.
    """
    __tablename__ = "meal_recommendations"
    
    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False, index=True)
    
    # Recommendation details
    daily_calories_target = Column(Integer, nullable=False)
    protein_target_g = Column(Integer)
    carbs_target_g = Column(Integer)
    fat_target_g = Column(Integer)
    
    # Meal plan details (breakfast, lunch, dinner, snacks)
    meal_plan = Column(JSON, nullable=False)  # Structured meal plan with food items
    
    # Nutritional summary
    total_calories = Column(Integer)
    total_protein_g = Column(Float)
    total_carbs_g = Column(Float)
    total_fat_g = Column(Float)
    
    # User feedback (to be used for reinforcement learning)
    user_rating = Column(Integer)  # 1-5 scale
    user_followed = Column(Boolean, default=None)  # True if user followed the plan
    user_feedback = Column(Text)  # Any text feedback from user
    
    # Recommendation metadata
    algorithm_version = Column(String)  # Version of the algorithm used
    criteria_weights = Column(JSON)  # Weights used in TOPSIS/AHP decision making
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    followed_at = Column(DateTime)  # When the user marked as followed
    
    # Health impact tracking
    symptoms_reported = Column(JSON)  # Any symptoms reported after following
    health_metrics_before = Column(JSON)  # User health metrics before recommendation
    health_metrics_after = Column(JSON)  # User health metrics after following
    
    def __repr__(self):
        return f"<MealRecommendation(id={self.id}, user_id={self.user_id}, calories={self.daily_calories_target})>"