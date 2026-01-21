import os
import numpy as np
import tensorflow as tf
import joblib
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List

# FastApi configuration
app = FastAPI(
    title="IoT Predictive Maintenance AI Service",
    description="A FastAPI service for predictive maintenance using TensorFlow models.",
    version="2.0.0"
)

# Model loading
MODEL_PATH = "models/best_rul_model.keras"
SCALER_PATH = "models/scaler.pkl"
model = None
scaler = None

# Data Structures in Pydantic

# Sensor reading structure
class SensorReading(BaseModel):
    vibration: float
    temperature: float
    current: float
# Request Pyload structure (temporal sequence of sensor readings)
# For the prediction we need not only the last value but a list of latest N values (e.g. last 50 cicles)
class PredictionRequest(BaseModel):
    asset_id: str
    sequence: List[SensorReading]

# Response Payload structure
class PredictionResponse(BaseModel):
    asset_id: str
    predicted_rul: float
    timestamp: str
    status: str # e.g. "OK" or "ERROR"


# Events
@app.on_event("startup")
def load_model():
    """
    Load the TensorFlow model at startup.
    This prevents loading the model for each request, improving performance.
    """
    global model, scaler
    try:
        if os.path.exists(MODEL_PATH):
            print(f"Loading Model from {MODEL_PATH}...")
            model = tf.keras.models.load_model(MODEL_PATH)
            print("Model loaded successfully.")
        else:
            print(f"Model file not found at {MODEL_PATH}.")

        if os.path.exists(SCALER_PATH):
            print(f"Loading Scaler from {SCALER_PATH}...")
            scaler = joblib.load(SCALER_PATH)
            print("Scaler loaded successfully.")
        else:
            print(f"Scaler file not found at {SCALER_PATH}.")
    except Exception as e:
        print(f"Error loading model: {e}")

# Endpoints
@app.get("/health")
def health_check():
    """
    Health check endpoint to verify if the service is running.
    """
    if model:
        return {"status": "online", "model_loaded": True}
    else:
        return {"status": "offline", "model_loaded": False}

@app.post("/predict-rul", response_model=PredictionResponse)
def predict_rul(payload: PredictionRequest):
    """
    Predict the Remaining Useful Life (RUL) of an asset based on sensor data.
    """
    if not model or not scaler:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Extraxtion and Data Preparation
        raw_matrix = np.array([
            [item.vibration, item.temperature, item.current] 
            for item in payload.sequence
        ])

        if raw_matrix.shape[0] != 50:
            raise HTTPException(status_code=400, detail="Input sequence must contain exactly 50 readings.")

        # Normalization
        normalized_matrix = scaler.transform(raw_matrix)

        # Dimension Control
        # RNN expects 3d input: (batch_size, time_steps, num_features)
        # batch_size = 1 (we predict one sequence at a time)
        # time_steps = len(payload.sequence)
        # num_features = 3 (vibration, temperature, current)

        # Reshape input data
        input_tensor = normalized_matrix.reshape(1, 50, 3)

        # Inference (Prediction)
        # model.predict return a tensor, we take the scalar value
        prediction_tensor = model.predict(input_tensor, verbose=0)
        rul_value = float(prediction_tensor[0][0])

        current_time = datetime.utcnow().isoformat()

        # Response 
        print(f"Predicted RUL for asset {payload.asset_id}: {rul_value}")

        return PredictionResponse(
            asset_id=payload.asset_id,
            predicted_rul=round(rul_value, 2),
            timestamp= current_time,
            status="OK"
        )

    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)