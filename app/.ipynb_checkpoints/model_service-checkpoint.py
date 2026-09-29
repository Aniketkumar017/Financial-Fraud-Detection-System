from pathlib import Path
import joblib
import pandas as pd

# ============================================================

# PATH CONFIGURATION

# ============================================================

# Project root:

# Financial-Fraud-Detection-System/

PROJECT_ROOT = Path(**file**).resolve().parent.parent

MODELS_DIR = PROJECT_ROOT / "models"

# ============================================================

# MODEL ARTIFACT PATHS

# ============================================================

LR_MODEL_PATH = MODELS_DIR / "logistic_regression.pkl"
RF_MODEL_PATH = MODELS_DIR / "random_forest.pkl"
PREPROCESSOR_PATH = MODELS_DIR / "preprocessor.pkl"
FEATURES_PATH = MODELS_DIR / "final_features.pkl"
LR_THRESHOLD_PATH = MODELS_DIR / "lr_threshold.pkl"
RF_THRESHOLD_PATH = MODELS_DIR / "rf_threshold.pkl"

# ============================================================

# LOAD MODEL ARTIFACTS

# ============================================================

def load_artifact(path):
"""
Load a saved joblib artifact.
"""
if not path.exists():
raise FileNotFoundError(
f"Required model artifact not found: {path}"
)

```
return joblib.load(path)
```

# Load Logistic Regression

lr_model = load_artifact(LR_MODEL_PATH)

# Load Random Forest

rf_model = load_artifact(RF_MODEL_PATH)

# Load preprocessing pipeline

preprocessor = load_artifact(PREPROCESSOR_PATH)

# Load final feature list

final_features = load_artifact(FEATURES_PATH)

# Load validation-selected thresholds

lr_threshold = float(load_artifact(LR_THRESHOLD_PATH))
rf_threshold = float(load_artifact(RF_THRESHOLD_PATH))

# ============================================================

# MODEL INFORMATION

# ============================================================

MODEL_NAME = "Logistic Regression"

# ============================================================

# VALIDATE INPUT FEATURES

# ============================================================

def validate_features(data):
"""
Check whether all model-required features are present.
"""

```
missing_features = [
    feature
    for feature in final_features
    if feature not in data.columns
]

if missing_features:
    raise ValueError(
        "Missing required features: "
        + ", ".join(missing_features)
    )

return True
```

# ============================================================

# PREPARE MODEL INPUT

# ============================================================

def prepare_input(data):
"""
Prepare input data according to the saved feature list
and preprocessing pipeline.
"""

```
if isinstance(data, dict):
    data = pd.DataFrame([data])

elif isinstance(data, pd.Series):
    data = data.to_frame().T

elif not isinstance(data, pd.DataFrame):
    raise TypeError(
        "Input must be a dictionary, pandas Series, "
        "or pandas DataFrame."
    )

validate_features(data)

# Keep exactly the features used during training
X = data[final_features].copy()

# Apply the SAME preprocessing fitted during training
X_processed = preprocessor.transform(X)

return X_processed
```

# ============================================================

# PREDICT FRAUD PROBABILITY

# ============================================================

def predict_fraud(data):
"""
Generate fraud probability and classification
using Logistic Regression.
"""

```
X_processed = prepare_input(data)

fraud_probability = float(
    lr_model.predict_proba(X_processed)[0, 1]
)

predicted_fraud = int(
    fraud_probability >= lr_threshold
)

return {
    "fraud_probability": fraud_probability,
    "predicted_fraud": predicted_fraud,
    "threshold": lr_threshold,
    "model": MODEL_NAME
}
```

# ============================================================

# RISK LEVEL

# ============================================================

def get_risk_level(fraud_probability):
"""
Convert fraud probability into business risk categories.
"""

```
if fraud_probability < 0.20:
    return "Low Risk"

elif fraud_probability < 0.50:
    return "Medium Risk"

elif fraud_probability < 0.80:
    return "High Risk"

else:
    return "Critical Risk"
```

# ============================================================

# REASON OF RISK

# ============================================================

def get_risk_reasons(data):
"""
Generate understandable risk reasons from transaction
and behavioural indicators.

```
These are rule-based explanations of observed risk signals.
They are not causal explanations of the ML model.
"""

if isinstance(data, dict):
    data = pd.DataFrame([data])

reasons = []

row = data.iloc[0]

# Transaction amount
if "amount_to_monthly_spend" in row.index:
    if pd.notna(row["amount_to_monthly_spend"]):
        if row["amount_to_monthly_spend"] >= 2:
            reasons.append(
                "Transaction amount is unusually high compared "
                "with monthly spending"
            )

# Transaction velocity
if "txn_count_1h" in row.index:
    if pd.notna(row["txn_count_1h"]):
        if row["txn_count_1h"] >= 5:
            reasons.append(
                "High number of transactions in the last hour"
            )

if "txn_count_24h" in row.index:
    if pd.notna(row["txn_count_24h"]):
        if row["txn_count_24h"] >= 15:
            reasons.append(
                "High transaction activity in the last 24 hours"
            )

# Failed transactions
if "failed_txn_count_24h" in row.index:
    if pd.notna(row["failed_txn_count_24h"]):
        if row["failed_txn_count_24h"] >= 3:
            reasons.append(
                "Multiple failed transactions detected recently"
            )

# IP risk
if "ip_risk_score" in row.index:
    if pd.notna(row["ip_risk_score"]):
        if row["ip_risk_score"] >= 0.70:
            reasons.append(
                "High IP risk detected"
            )

# Merchant risk
if "merchant_risk_score" in row.index:
    if pd.notna(row["merchant_risk_score"]):
        if row["merchant_risk_score"] >= 0.70:
            reasons.append(
                "High merchant risk detected"
            )

# Geographic distance
if "geo_distance_from_last_txn" in row.index:
    if pd.notna(row["geo_distance_from_last_txn"]):
        if row["geo_distance_from_last_txn"] >= 500:
            reasons.append(
                "Large geographic distance from the previous transaction"
            )

# Customer fraud history
if "customer_prev_fraud_count" in row.index:
    if pd.notna(row["customer_prev_fraud_count"]):
        if row["customer_prev_fraud_count"] > 0:
            reasons.append(
                "Previous fraud activity associated with the customer"
            )

# Merchant fraud history
if "merchant_prev_fraud_count" in row.index:
    if pd.notna(row["merchant_prev_fraud_count"]):
        if row["merchant_prev_fraud_count"] > 0:
            reasons.append(
                "Previous fraud activity associated with the merchant"
            )

# International transaction
if "is_international" in row.index:
    if row["is_international"] == 1:
        reasons.append(
            "International transaction detected"
        )

# High velocity engineered feature
if "high_velocity_1h" in row.index:
    if row["high_velocity_1h"] == 1:
        reasons.append(
            "Transaction velocity is unusually high"
        )

# Multiple failures engineered feature
if "multiple_failures" in row.index:
    if row["multiple_failures"] == 1:
        reasons.append(
            "Multiple recent transaction failures detected"
        )

# Default message
if not reasons:
    reasons.append(
        "No major individual risk signal was identified"
    )

return reasons
```

# ============================================================

# RECOMMENDED ACTION

# ============================================================

def get_recommended_action(risk_level):
"""
Provide a business recommendation based on risk level.
"""

```
actions = {
    "Low Risk": {
        "action": "ALLOW",
        "message": "Transaction can proceed with normal monitoring."
    },

    "Medium Risk": {
        "action": "MONITOR",
        "message": "Allow transaction and continue monitoring."
    },

    "High Risk": {
        "action": "ADDITIONAL VERIFICATION",
        "message": "Perform additional customer verification before proceeding."
    },

    "Critical Risk": {
        "action": "MANUAL REVIEW",
        "message": "Temporarily hold the transaction and require manual review."
    }
}

return actions.get(
    risk_level,
    {
        "action": "MANUAL REVIEW",
        "message": "Manual review recommended."
    }
)
```

# ============================================================

# COMPLETE TRANSACTION ANALYSIS

# ============================================================

def analyze_transaction(data):
"""
Complete fraud risk analysis.

```
Returns:
    - fraud probability
    - prediction
    - risk level
    - reasons
    - recommended action
    - model information
"""

prediction = predict_fraud(data)

probability = prediction["fraud_probability"]

risk_level = get_risk_level(probability)

reasons = get_risk_reasons(data)

recommended_action = get_recommended_action(risk_level)

return {
    "fraud_probability": round(probability * 100, 2),
    "predicted_fraud": prediction["predicted_fraud"],
    "risk_level": risk_level,
    "risk_reasons": reasons,
    "recommended_action": recommended_action["action"],
    "recommended_action_message": recommended_action["message"],
    "threshold": round(prediction["threshold"], 4),
    "model": prediction["model"]
}
```

# ============================================================

# MODEL STATUS

# ============================================================

def get_model_status():
"""
Return information about loaded model artifacts.
"""

```
return {
    "model": MODEL_NAME,
    "logistic_regression_loaded": lr_model is not None,
    "random_forest_loaded": rf_model is not None,
    "preprocessor_loaded": preprocessor is not None,
    "features_loaded": final_features is not None,
    "number_of_features": len(final_features),
    "lr_threshold": lr_threshold,
    "rf_threshold": rf_threshold
}