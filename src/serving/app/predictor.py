"""
Model Predictor - Loads and serves ML models from MLflow
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import mlflow
from mlflow.tracking import MlflowClient
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChurnPredictor:
    """
    Handles model loading and predictions for churn models
    Supports multiple model versions for A/B testing
    """
    
    def __init__(self):
        self.mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow.mlflow.svc.cluster.local:5000')
        self.models = {}
        self.scalers = {}
        self.model_info = {}
        self._loaded = False
        
        # Feature configuration
        self.numeric_features = [
            'tenure_months', 'tenure_years', 'monthly_charges', 'total_charges',
            'avg_monthly_charge', 'charge_per_tenure', 'total_services', 'risk_score'
        ]
        self.binary_features = [
            'is_new_customer', 'is_loyal_customer', 'contract_month_to_month',
            'contract_one_year', 'contract_two_year', 'payment_electronic',
            'payment_auto', 'has_internet', 'has_fiber', 'is_senior',
            'has_partner', 'has_dependents', 'paperless_billing',
            'has_security', 'has_support', 'has_streaming'
        ]
        self.all_features = self.numeric_features + self.binary_features
        
    def load_models(self):
        """Load models from MLflow registry"""
        try:
            mlflow.set_tracking_uri(self.mlflow_uri)
            client = MlflowClient()
            
            # Load models for A/B testing
            model_names = [
                "telco-churn-random_forest",
                "telco-churn-gradient_boosting",
                "telco-churn-logistic_regression"
            ]
            
            for model_name in model_names:
                try:
                    # Try to load production model first
                    model_uri = f"models:/{model_name}/Production"
                    model = mlflow.sklearn.load_model(model_uri)
                    
                    # Get model version info
                    versions = client.search_model_versions(f"name='{model_name}'")
                    prod_version = next(
                        (v for v in versions if v.current_stage == "Production"),
                        versions[0] if versions else None
                    )
                    
                    self.models[model_name] = model
                    self.model_info[model_name] = {
                        "version": prod_version.version if prod_version else "unknown",
                        "stage": "Production",
                        "run_id": prod_version.run_id if prod_version else "unknown"
                    }
                    
                    logger.info(f"Loaded {model_name} (Production, v{self.model_info[model_name]['version']})")
                    
                except Exception as e:
                    # Try loading latest version
                    try:
                        model_uri = f"models:/{model_name}/latest"
                        model = mlflow.sklearn.load_model(model_uri)
                        self.models[model_name] = model
                        self.model_info[model_name] = {
                            "version": "latest",
                            "stage": "None",
                            "run_id": "unknown"
                        }
                        logger.info(f"Loaded {model_name} (latest)")
                    except Exception as e2:
                        logger.warning(f"Could not load {model_name}: {e2}")
            
            if not self.models:
                # Fallback: create a simple model if no models found
                logger.warning("No models found in MLflow, using fallback model")
                self._create_fallback_model()
            
            self._loaded = True
            logger.info(f"Loaded {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self._create_fallback_model()
            self._loaded = True
    
    def _create_fallback_model(self):
        """Create a simple fallback model for demonstration"""
        from sklearn.linear_model import LogisticRegression
        
        # Create a simple model with fixed coefficients
        model = LogisticRegression()
        # Simulate fitted model
        n_features = len(self.all_features)
        model.classes_ = np.array([0, 1])
        model.coef_ = np.random.randn(1, n_features) * 0.1
        model.intercept_ = np.array([-0.5])
        
        self.models["fallback-model"] = model
        self.model_info["fallback-model"] = {
            "version": "1.0",
            "stage": "Fallback",
            "run_id": "local"
        }
        logger.info("Created fallback model")
    
    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return self._loaded and len(self.models) > 0
    
    def _preprocess_input(self, customer_data: Dict[str, Any]) -> pd.DataFrame:
        """Transform customer input to model features"""
        
        # Extract and compute features
        tenure = customer_data.get('tenure_months', 0)
        monthly = customer_data.get('monthly_charges', 0)
        total = customer_data.get('total_charges', 0)
        contract = customer_data.get('contract_type', 'Month-to-month')
        payment = customer_data.get('payment_method', '')
        internet = customer_data.get('internet_service', 'No')
        
        features = {
            # Numeric features
            'tenure_months': tenure,
            'tenure_years': tenure / 12,
            'monthly_charges': monthly,
            'total_charges': total,
            'avg_monthly_charge': total / (tenure + 1),
            'charge_per_tenure': monthly / (tenure + 1),
            'total_services': sum([
                customer_data.get('has_phone', False),
                customer_data.get('has_online_security', False),
                customer_data.get('has_tech_support', False),
                customer_data.get('has_streaming', False),
                internet != 'No'
            ]),
            'risk_score': self._calculate_risk_score(customer_data),
            
            # Binary features
            'is_new_customer': int(tenure <= 6),
            'is_loyal_customer': int(tenure >= 24),
            'contract_month_to_month': int(contract == 'Month-to-month'),
            'contract_one_year': int(contract == 'One year'),
            'contract_two_year': int(contract == 'Two year'),
            'payment_electronic': int('electronic' in payment.lower()),
            'payment_auto': int('automatic' in payment.lower()),
            'has_internet': int(internet != 'No'),
            'has_fiber': int(internet == 'Fiber optic'),
            'is_senior': int(customer_data.get('is_senior', False)),
            'has_partner': int(customer_data.get('has_partner', False)),
            'has_dependents': int(customer_data.get('has_dependents', False)),
            'paperless_billing': int(customer_data.get('paperless_billing', False)),
            'has_security': int(customer_data.get('has_online_security', False)),
            'has_support': int(customer_data.get('has_tech_support', False)),
            'has_streaming': int(customer_data.get('has_streaming', False))
        }
        
        # Create DataFrame in correct order
        df = pd.DataFrame([features])[self.all_features]
        return df
    
    def _calculate_risk_score(self, data: Dict[str, Any]) -> float:
        """Calculate heuristic risk score"""
        score = 0
        
        # Contract risk
        if data.get('contract_type') == 'Month-to-month':
            score += 3
        
        # Payment risk
        if 'electronic' in data.get('payment_method', '').lower():
            score += 2
        
        # Tenure risk
        if data.get('tenure_months', 0) <= 6:
            score += 2
        elif data.get('tenure_months', 0) >= 24:
            score -= 2
        
        # Service risk
        if not data.get('has_tech_support', False):
            score += 1
        
        if data.get('internet_service') == 'Fiber optic':
            score += 1
        
        return score
    
    def _get_risk_level(self, probability: float) -> str:
        """Categorize churn probability into risk levels"""
        if probability >= 0.7:
            return "HIGH"
        elif probability >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def predict(self, customer_data: Dict[str, Any], model_name: Optional[str] = None) -> Dict[str, Any]:
        """Make a churn prediction"""
        
        # Select model
        if model_name and model_name in self.models:
            model = self.models[model_name]
            info = self.model_info[model_name]
        else:
            # Use first available model
            model_name = list(self.models.keys())[0]
            model = self.models[model_name]
            info = self.model_info[model_name]
        
        # Preprocess input
        features = self._preprocess_input(customer_data)
        
        # Make prediction
        probability = model.predict_proba(features)[0][1]
        prediction = probability >= 0.5
        
        return {
            "probability": float(probability),
            "prediction": bool(prediction),
            "risk_level": self._get_risk_level(probability),
            "model_name": model_name,
            "model_version": info["version"]
        }
    
    def predict_with_explanation(self, customer_data: Dict[str, Any], model_name: Optional[str] = None) -> Dict[str, Any]:
        """Make prediction with feature importance explanation"""
        
        # Get base prediction
        result = self.predict(customer_data, model_name)
        
        # Select model
        if model_name and model_name in self.models:
            model = self.models[model_name]
        else:
            model_name = list(self.models.keys())[0]
            model = self.models[model_name]
        
        # Get feature importance
        features = self._preprocess_input(customer_data)
        
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_[0])
        else:
            importance = np.ones(len(self.all_features)) / len(self.all_features)
        
        # Create feature importance dict
        feature_importance = {
            name: float(imp) 
            for name, imp in zip(self.all_features, importance)
        }
        
        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Get top risk factors
        feature_values = features.iloc[0].to_dict()
        top_risk_factors = []
        
        for feature, importance_val in sorted_features[:5]:
            value = feature_values[feature]
            top_risk_factors.append({
                "feature": feature,
                "value": value,
                "importance": importance_val,
                "contribution": "increases" if value > 0.5 else "decreases"
            })
        
        result["feature_importance"] = dict(sorted_features)
        result["top_risk_factors"] = top_risk_factors
        
        return result
    
    def get_model_info(self) -> List[Dict[str, Any]]:
        """Get information about loaded models"""
        info_list = []
        
        for name, info in self.model_info.items():
            info_list.append({
                "model_name": name,
                "model_version": info["version"],
                "stage": info["stage"],
                "metrics": {},  # Would be populated from MLflow
                "is_active": True,
                "traffic_percentage": 100 / len(self.models) if self.models else 0
            })
        
        return info_list

