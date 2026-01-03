"""
A/B Testing Router
Routes traffic between different model versions
"""

import os
import random
import logging
from typing import Tuple, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ABRouter:
    """
    A/B Testing traffic router for ML models
    Supports configurable traffic splits between model versions
    """
    
    def __init__(self):
        # Default configuration
        self.model_a_name = "telco-churn-random_forest"
        self.model_b_name = "telco-churn-gradient_boosting"
        
        # Traffic weights (0.0 to 1.0)
        self.model_a_weight = 0.8  # Champion gets 80%
        self.model_b_weight = 0.2  # Challenger gets 20%
        
        self.enabled = True
        
    def configure_from_env(self):
        """Configure from environment variables"""
        self.model_a_name = os.getenv('AB_MODEL_A', self.model_a_name)
        self.model_b_name = os.getenv('AB_MODEL_B', self.model_b_name)
        self.model_a_weight = float(os.getenv('AB_MODEL_A_WEIGHT', self.model_a_weight))
        self.model_b_weight = float(os.getenv('AB_MODEL_B_WEIGHT', self.model_b_weight))
        self.enabled = os.getenv('AB_ENABLED', 'true').lower() == 'true'
        
        # Normalize weights
        total = self.model_a_weight + self.model_b_weight
        if total > 0:
            self.model_a_weight /= total
            self.model_b_weight /= total
        
        logger.info(f"A/B Router configured: {self.model_a_name}={self.model_a_weight:.0%}, {self.model_b_name}={self.model_b_weight:.0%}")
    
    def get_model(self) -> Tuple[str, str]:
        """
        Get model name based on A/B routing
        Returns: (model_name, ab_group)
        """
        if not self.enabled:
            return self.model_a_name, "control"
        
        # Random routing based on weights
        if random.random() < self.model_a_weight:
            return self.model_a_name, "A"
        else:
            return self.model_b_name, "B"
    
    def get_traffic_split(self) -> Dict[str, float]:
        """Get current traffic split configuration"""
        return {
            self.model_a_name: self.model_a_weight,
            self.model_b_name: self.model_b_weight
        }
    
    def update_weights(self, model_a_weight: float, model_b_weight: float):
        """Update traffic split weights"""
        # Normalize
        total = model_a_weight + model_b_weight
        if total > 0:
            self.model_a_weight = model_a_weight / total
            self.model_b_weight = model_b_weight / total
        
        logger.info(f"Updated weights: {self.model_a_name}={self.model_a_weight:.0%}, {self.model_b_name}={self.model_b_weight:.0%}")
    
    def set_models(self, model_a: str, model_b: str):
        """Set model names for A/B testing"""
        self.model_a_name = model_a
        self.model_b_name = model_b
        logger.info(f"Set A/B models: A={model_a}, B={model_b}")
    
    def enable(self):
        """Enable A/B testing"""
        self.enabled = True
        logger.info("A/B testing enabled")
    
    def disable(self):
        """Disable A/B testing (all traffic goes to model A)"""
        self.enabled = False
        logger.info("A/B testing disabled")

