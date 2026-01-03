"""
FastAPI Model Serving Application with A/B Testing
Serves Telco Customer Churn predictions
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import os
import random
import time
import logging
from datetime import datetime
from collections import defaultdict
import json

from .predictor import ChurnPredictor
from .ab_router import ABRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Telco Churn Prediction API",
    description="Production ML API with A/B testing for customer churn prediction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor and A/B router
predictor = ChurnPredictor()
ab_router = ABRouter()

# Metrics storage
metrics = defaultdict(lambda: defaultdict(int))
latencies = defaultdict(list)

# Request/Response Models
class CustomerData(BaseModel):
    """Customer data for churn prediction"""
    customer_id: str = Field(..., description="Unique customer identifier")
    tenure_months: float = Field(..., ge=0, description="Months as customer")
    monthly_charges: float = Field(..., ge=0, description="Monthly charges in $")
    total_charges: float = Field(..., ge=0, description="Total charges in $")
    contract_type: str = Field(..., description="Contract type: Month-to-month, One year, Two year")
    payment_method: str = Field(..., description="Payment method")
    internet_service: str = Field(..., description="Internet service type")
    has_phone: bool = Field(default=True, description="Has phone service")
    has_partner: bool = Field(default=False, description="Has partner")
    has_dependents: bool = Field(default=False, description="Has dependents")
    is_senior: bool = Field(default=False, description="Is senior citizen")
    has_online_security: bool = Field(default=False, description="Has online security")
    has_tech_support: bool = Field(default=False, description="Has tech support")
    has_streaming: bool = Field(default=False, description="Has streaming services")
    paperless_billing: bool = Field(default=False, description="Uses paperless billing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST001",
                "tenure_months": 12,
                "monthly_charges": 79.99,
                "total_charges": 959.88,
                "contract_type": "Month-to-month",
                "payment_method": "Electronic check",
                "internet_service": "Fiber optic",
                "has_phone": True,
                "has_partner": False,
                "has_dependents": False,
                "is_senior": False,
                "has_online_security": False,
                "has_tech_support": False,
                "has_streaming": True,
                "paperless_billing": True
            }
        }

class PredictionResponse(BaseModel):
    """Prediction response"""
    customer_id: str
    churn_probability: float
    churn_prediction: bool
    risk_level: str
    model_version: str
    model_name: str
    prediction_time_ms: float
    timestamp: str
    ab_group: str

class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    customers: List[CustomerData]

class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[PredictionResponse]
    total_processed: int
    avg_prediction_time_ms: float

class ModelInfo(BaseModel):
    """Model information"""
    model_name: str
    model_version: str
    stage: str
    metrics: Dict[str, float]
    is_active: bool
    traffic_percentage: float

class ABStats(BaseModel):
    """A/B testing statistics"""
    total_requests: int
    model_a_requests: int
    model_b_requests: int
    model_a_avg_latency_ms: float
    model_b_avg_latency_ms: float
    model_a_name: str
    model_b_name: str
    traffic_split: Dict[str, float]

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    logger.info("Starting Telco Churn Prediction API...")
    try:
        predictor.load_models()
        ab_router.configure_from_env()
        logger.info("Models loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models_loaded": predictor.is_loaded(),
        "version": "1.0.0"
    }

# Readiness check
@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not predictor.is_loaded():
        raise HTTPException(status_code=503, detail="Models not loaded")
    return {"status": "ready"}

# Single prediction
@app.post("/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict(customer: CustomerData):
    """
    Make a churn prediction for a single customer.
    Uses A/B testing to route between models.
    """
    start_time = time.time()
    
    try:
        # Get A/B routing decision
        model_choice, ab_group = ab_router.get_model()
        
        # Make prediction
        result = predictor.predict(customer.model_dump(), model_choice)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Track metrics
        metrics[model_choice]["requests"] += 1
        latencies[model_choice].append(latency_ms)
        
        response = PredictionResponse(
            customer_id=customer.customer_id,
            churn_probability=result["probability"],
            churn_prediction=result["prediction"],
            risk_level=result["risk_level"],
            model_version=result["model_version"],
            model_name=result["model_name"],
            prediction_time_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat(),
            ab_group=ab_group
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch prediction
@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch(request: BatchPredictionRequest):
    """Make churn predictions for multiple customers"""
    predictions = []
    total_time = 0
    
    for customer in request.customers:
        start_time = time.time()
        model_choice, ab_group = ab_router.get_model()
        result = predictor.predict(customer.model_dump(), model_choice)
        latency_ms = (time.time() - start_time) * 1000
        total_time += latency_ms
        
        predictions.append(PredictionResponse(
            customer_id=customer.customer_id,
            churn_probability=result["probability"],
            churn_prediction=result["prediction"],
            risk_level=result["risk_level"],
            model_version=result["model_version"],
            model_name=result["model_name"],
            prediction_time_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat(),
            ab_group=ab_group
        ))
    
    return BatchPredictionResponse(
        predictions=predictions,
        total_processed=len(predictions),
        avg_prediction_time_ms=total_time / len(predictions) if predictions else 0
    )

# Prediction with explanation
@app.post("/predict/explain", tags=["Predictions"])
async def predict_with_explanation(customer: CustomerData):
    """Make a prediction with feature importance explanation"""
    model_choice, ab_group = ab_router.get_model()
    result = predictor.predict_with_explanation(customer.model_dump(), model_choice)
    
    return {
        "customer_id": customer.customer_id,
        "prediction": result["prediction"],
        "probability": result["probability"],
        "risk_level": result["risk_level"],
        "feature_importance": result["feature_importance"],
        "top_risk_factors": result["top_risk_factors"],
        "model_name": result["model_name"],
        "ab_group": ab_group,
        "timestamp": datetime.utcnow().isoformat()
    }

# Model information
@app.get("/models", response_model=List[ModelInfo], tags=["Models"])
async def get_models():
    """Get information about deployed models"""
    return predictor.get_model_info()

# A/B testing statistics
@app.get("/ab-stats", response_model=ABStats, tags=["A/B Testing"])
async def get_ab_stats():
    """Get A/B testing statistics"""
    model_a = ab_router.model_a_name
    model_b = ab_router.model_b_name
    
    model_a_requests = metrics[model_a]["requests"]
    model_b_requests = metrics[model_b]["requests"]
    
    return ABStats(
        total_requests=model_a_requests + model_b_requests,
        model_a_requests=model_a_requests,
        model_b_requests=model_b_requests,
        model_a_avg_latency_ms=sum(latencies[model_a]) / len(latencies[model_a]) if latencies[model_a] else 0,
        model_b_avg_latency_ms=sum(latencies[model_b]) / len(latencies[model_b]) if latencies[model_b] else 0,
        model_a_name=model_a,
        model_b_name=model_b,
        traffic_split=ab_router.get_traffic_split()
    )

# Update A/B configuration
@app.post("/ab-config", tags=["A/B Testing"])
async def update_ab_config(model_a_weight: float = 0.5, model_b_weight: float = 0.5):
    """Update A/B testing traffic split"""
    ab_router.update_weights(model_a_weight, model_b_weight)
    return {
        "message": "A/B configuration updated",
        "traffic_split": ab_router.get_traffic_split()
    }

# Metrics endpoint (Prometheus format)
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get metrics in Prometheus format"""
    output = []
    
    for model_name, model_metrics in metrics.items():
        output.append(f'prediction_requests_total{{model="{model_name}"}} {model_metrics["requests"]}')
        
        if latencies[model_name]:
            avg_latency = sum(latencies[model_name]) / len(latencies[model_name])
            output.append(f'prediction_latency_avg_ms{{model="{model_name}"}} {avg_latency:.2f}')
    
    return "\n".join(output)

# Root endpoint
@app.get("/", tags=["Info"])
async def root():
    """API root - returns basic info"""
    return {
        "name": "Telco Churn Prediction API",
        "version": "1.0.0",
        "description": "Production ML API with A/B testing",
        "endpoints": {
            "predict": "/predict",
            "batch_predict": "/predict/batch",
            "explain": "/predict/explain",
            "models": "/models",
            "ab_stats": "/ab-stats",
            "health": "/health",
            "docs": "/docs"
        }
    }

