import os
import pickle
from typing import Optional

from fastapi import FastAPI, HTTPException

from config import (
    API_HOST,
    API_PORT,
    ALERT_THRESHOLD,
    MODEL_PATH,
)
from feature_engineering import features_to_array
from schemas import ScoreRequest, ScoreResponse

app = FastAPI(title="Retail Stock-Out Risk API")

model_bundle = None
model_file_last_modified: Optional[float] = None


def load_model_if_needed():
    global model_bundle
    global model_file_last_modified

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}. Run train_model.py first."
        )

    current_modified_time = os.path.getmtime(MODEL_PATH)

    if model_bundle is None or model_file_last_modified != current_modified_time:
        with open(MODEL_PATH, "rb") as f:
            model_bundle = pickle.load(f)

        required_keys = {"scaler", "classifier", "model_name", "feature_columns"}
        missing_keys = required_keys - set(model_bundle.keys())

        if missing_keys:
            raise ValueError(
                f"Invalid model bundle. Missing keys: {sorted(missing_keys)}"
            )

        model_file_last_modified = current_modified_time
        print(f"Model bundle loaded from {MODEL_PATH}")

    return model_bundle


@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest):
    try:
        bundle = load_model_if_needed()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))

    features = request.model_dump()
    X = features_to_array(features)

    try:
        scaler = bundle["scaler"]
        classifier = bundle["classifier"]

        X_scaled = scaler.transform(X)

        probability = float(classifier.predict_proba(X_scaled)[0][1])

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model scoring failed: {e}",
        )

    stockout_risk = probability >= ALERT_THRESHOLD

    return {
        "stockout_risk": bool(stockout_risk),
        "stockout_probability": round(probability, 4),
        "model": bundle["model_name"],
    }


@app.get("/health")
def health():
    model_exists = os.path.exists(MODEL_PATH)

    return {
        "status": "ok",
        "model_exists": model_exists,
        "model_loaded": model_bundle is not None,
        "model_path": MODEL_PATH,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
    )