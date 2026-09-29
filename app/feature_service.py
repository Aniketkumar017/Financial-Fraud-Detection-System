import pandas as pd
import numpy as np

# ============================================================

# BASIC VALIDATION

# ============================================================

def validate_transaction_input(data):
"""
Validate the simple transaction information received
from the application form.
"""

```
required_fields = [
    "transaction_amount",
    "payment_channel",
    "device_type",
    "is_international",
    "account_age_days",
    "credit_score_band",
    "kyc_level",
    "avg_monthly_spend",
    "merchant_risk_score",
    "ip_risk_score",
    "txn_count_1h",
    "txn_count_24h",
    "failed_txn_count_24h",
    "geo_distance_from_last_txn",
    "amount_deviation_from_user_mean"
]

missing_fields = [
    field for field in required_fields
    if field not in data
]

if missing_fields:
    raise ValueError(
        "Missing input fields: "
        + ", ".join(missing_fields)
    )

if float(data["transaction_amount"]) < 0:
    raise ValueError(
        "Transaction amount cannot be negative."
    )

if float(data["account_age_days"]) < 0:
    raise ValueError(
        "Account age cannot be negative."
    )

if float(data["avg_monthly_spend"]) < 0:
    raise ValueError(
        "Average monthly spending cannot be negative."
    )

if int(data["txn_count_1h"]) < 0:
    raise ValueError(
        "Transaction count cannot be negative."
    )

if int(data["txn_count_24h"]) < 0:
    raise ValueError(
        "Transaction count cannot be negative."
    )

if int(data["failed_txn_count_24h"]) < 0:
    raise ValueError(
        "Failed transaction count cannot be negative."
    )

if float(data["geo_distance_from_last_txn"]) < 0:
    raise ValueError(
        "Geographic distance cannot be negative."
    )

return True
```

# ============================================================

# CREATE BASE TRANSACTION DATA

# ============================================================

def create_base_transaction(data):
"""
Convert the user-friendly application input into
the raw transaction structure expected by the
existing feature engineering pipeline.
"""

```
validate_transaction_input(data)

transaction = {
    "transaction_id": data.get(
        "transaction_id",
        "APP_TRANSACTION"
    ),

    "transaction_time": data.get(
        "transaction_time",
        pd.Timestamp.now()
    ),

    "customer_id": data.get(
        "customer_id",
        "APP_CUSTOMER"
    ),

    "merchant_id": data.get(
        "merchant_id",
        "APP_MERCHANT"
    ),

    "account_age_days": float(
        data["account_age_days"]
    ),

    "credit_score_band": int(
        data["credit_score_band"]
    ),

    "kyc_level": int(
        data["kyc_level"]
    ),

    "avg_monthly_spend": float(
        data["avg_monthly_spend"]
    ),

    "merchant_risk_score": float(
        data["merchant_risk_score"]
    ),

    "transaction_amount": float(
        data["transaction_amount"]
    ),

    "payment_channel": data[
        "payment_channel"
    ],

    "device_type": data[
        "device_type"
    ],

    "is_international": int(
        data["is_international"]
    ),

    "ip_risk_score": float(
        data["ip_risk_score"]
    ),

    "txn_count_1h": int(
        data["txn_count_1h"]
    ),

    "txn_count_24h": int(
        data["txn_count_24h"]
    ),

    "failed_txn_count_24h": int(
        data["failed_txn_count_24h"]
    ),

    "geo_distance_from_last_txn": float(
        data["geo_distance_from_last_txn"]
    ),

    "amount_deviation_from_user_mean": float(
        data["amount_deviation_from_user_mean"]
    )
}

return pd.DataFrame([transaction])
```

# ============================================================

# TIME FEATURES

# ============================================================

def create_time_features(df):
"""
Create the same basic time features used in the
notebook pipeline.
"""

```
df = df.copy()

df["transaction_time"] = pd.to_datetime(
    df["transaction_time"]
)

df["hour"] = (
    df["transaction_time"].dt.hour
)

df["day"] = (
    df["transaction_time"].dt.dayofweek
)

df["month"] = (
    df["transaction_time"].dt.month
)

df["day_of_week"] = (
    df["transaction_time"].dt.dayofweek
)

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)

return df
```

# ============================================================

# HISTORICAL FEATURES

# ============================================================

def create_current_historical_features(
df,
customer_history=None,
merchant_history=None
):
"""
Create historical customer and merchant features
for a NEW transaction.

```
IMPORTANT:
The current transaction is NOT added to history.

customer_history and merchant_history should contain
information available before the current transaction.
"""

df = df.copy()

if customer_history is None:
    customer_history = {}

if merchant_history is None:
    merchant_history = {}

customer_prev_txn = []
customer_prev_fraud = []
customer_prev_avg_amount = []

merchant_prev_txn = []
merchant_prev_fraud = []
merchant_prev_avg_amount = []

for _, row in df.iterrows():

    customer_id = row["customer_id"]
    merchant_id = row["merchant_id"]

    # ----------------------------------------------------
    # Customer history
    # ----------------------------------------------------

    c_hist = customer_history.get(
        customer_id,
        {
            "txn": 0,
            "fraud": 0,
            "amount_sum": 0.0
        }
    )

    customer_prev_txn.append(
        c_hist["txn"]
    )

    customer_prev_fraud.append(
        c_hist["fraud"]
    )

    if c_hist["txn"] > 0:
        customer_prev_avg_amount.append(
            c_hist["amount_sum"]
            / c_hist["txn"]
        )
    else:
        customer_prev_avg_amount.append(
            np.nan
        )

    # ----------------------------------------------------
    # Merchant history
    # ----------------------------------------------------

    m_hist = merchant_history.get(
        merchant_id,
        {
            "txn": 0,
            "fraud": 0,
            "amount_sum": 0.0
        }
    )

    merchant_prev_txn.append(
        m_hist["txn"]
    )

    merchant_prev_fraud.append(
        m_hist["fraud"]
    )

    if m_hist["txn"] > 0:
        merchant_prev_avg_amount.append(
            m_hist["amount_sum"]
            / m_hist["txn"]
        )
    else:
        merchant_prev_avg_amount.append(
            np.nan
        )

df["customer_prev_txn_count"] = (
    customer_prev_txn
)

df["customer_prev_fraud_count"] = (
    customer_prev_fraud
)

df["customer_prev_avg_amount"] = (
    customer_prev_avg_amount
)

df["customer_prev_fraud_rate"] = np.where(
    df["customer_prev_txn_count"] > 0,
    df["customer_prev_fraud_count"]
    / df["customer_prev_txn_count"],
    0.0
)

df["merchant_prev_txn_count"] = (
    merchant_prev_txn
)

df["merchant_prev_fraud_count"] = (
    merchant_prev_fraud
)

df["merchant_prev_avg_amount"] = (
    merchant_prev_avg_amount
)

df["merchant_prev_fraud_rate"] = np.where(
    df["merchant_prev_txn_count"] > 0,
    df["merchant_prev_fraud_count"]
    / df["merchant_prev_txn_count"],
    0.0
)

return df
```

# ============================================================

# AMOUNT + SMOOTHED FRAUD FEATURES

# ============================================================

def create_behavior_features(df):
"""
Create the historical amount ratios and smoothed
fraud-rate features used by the model.
"""

```
df = df.copy()

# --------------------------------------------------------
# Amount ratios
# --------------------------------------------------------

df["customer_amount_ratio"] = (
    df["transaction_amount"]
    / (
        df["customer_prev_avg_amount"]
        \+ 1
    )
)

df["merchant_amount_ratio"] = (
    df["transaction_amount"]
    / (
        df["merchant_prev_avg_amount"]
        \+ 1
    )
)

# --------------------------------------------------------
# Smoothed fraud rates
# --------------------------------------------------------

alpha = 10

# Same prior used in the notebook for test processing
prior_fraud_rate = 0.02

df["customer_smoothed_fraud_rate"] = (
    df["customer_prev_fraud_count"]
    + alpha * prior_fraud_rate
) / (
    df["customer_prev_txn_count"]
    + alpha
)

df["merchant_smoothed_fraud_rate"] = (
    df["merchant_prev_fraud_count"]
    + alpha * prior_fraud_rate
) / (
    df["merchant_prev_txn_count"]
    + alpha
)

return df
```

# ============================================================

# SAFE NUMERIC CLEANUP

# ============================================================

def clean_numeric_values(df):
"""
Replace infinite values with NaN.

```
The saved preprocessing pipeline handles missing values
using the training-time median imputation.
"""

df = df.copy()

numeric_columns = df.select_dtypes(
    include=np.number
).columns

df[numeric_columns] = (
    df[numeric_columns]
    .replace([np.inf, -np.inf], np.nan)
)

return df
```

# ============================================================

# FINAL FEATURE PREPARATION

# ============================================================

def prepare_features(
data,
customer_history=None,
merchant_history=None
):
"""
Complete feature preparation pipeline for one
application transaction.

```
Flow:

Simple User Input
      ↓
Base Transaction
      ↓
Time Features
      ↓
Historical Features
      ↓
Behaviour Features
      ↓
Engineered Features
      ↓
Model-ready DataFrame
"""

# --------------------------------------------------------
# 1. Create base transaction
# --------------------------------------------------------

df = create_base_transaction(data)

# --------------------------------------------------------
# 2. Time features
# --------------------------------------------------------

df = create_time_features(df)

# --------------------------------------------------------
# 3. Historical features
# --------------------------------------------------------

df = create_current_historical_features(
    df,
    customer_history=customer_history,
    merchant_history=merchant_history
)

# --------------------------------------------------------
# 4. Amount + fraud behaviour features
# --------------------------------------------------------

df = create_behavior_features(df)

# --------------------------------------------------------
# 5. Use the existing project feature engineering
# --------------------------------------------------------

try:

    from utils.feature_engg import (
        create_engineered_features
    )

    df = create_engineered_features(df)

except ImportError:

    raise ImportError(
        "Could not import create_engineered_features "
        "from app/utils/feature_engg.py. "
        "Make sure the existing feature engineering "
        "file is present."
    )

# --------------------------------------------------------
# 6. Clean infinite values
# --------------------------------------------------------

df = clean_numeric_values(df)

return df
```

# ============================================================

# MODEL FEATURE CHECK

# ============================================================

def select_model_features(
df,
final_features
):
"""
Select exactly the same 63 features used by the model.
"""

```
missing_features = [
    feature
    for feature in final_features
    if feature not in df.columns
]

if missing_features:

    raise ValueError(
        "Feature engineering did not create "
        "the following required model features: "
        + ", ".join(missing_features)
    )

return df[final_features].copy()
```

# ============================================================

# COMPLETE PIPELINE

# ============================================================

def build_model_input(
data,
final_features,
customer_history=None,
merchant_history=None
):
"""
Build the final 63-feature DataFrame required
by model_service.py.
"""

```
engineered_df = prepare_features(
    data,
    customer_history=customer_history,
    merchant_history=merchant_history
)

model_input = select_model_features(
    engineered_df,
    final_features
)

return model_input, engineered_df