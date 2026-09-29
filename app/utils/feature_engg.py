# ============================================================
# FINANCIAL FRAUD DETECTION SYSTEM
# FEATURE ENGINEERING
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# MAIN FEATURE ENGINEERING FUNCTION
# ============================================================

def create_engineered_features(df):
    """
    Create all engineered features used by the fraud detection
    machine learning models.

    This function follows the feature engineering logic used
    during model development in the notebook.

    Parameters
    ----------
    df : pandas.DataFrame
        Input transaction dataframe.

    Returns
    -------
    pandas.DataFrame
        Dataframe containing engineered features.
    """

    # Always work on a copy
    df = df.copy()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    required_columns = [
        "transaction_time",
        "transaction_amount",
        "avg_monthly_spend",
        "amount_deviation_from_user_mean",
        "txn_count_1h",
        "txn_count_24h",
        "failed_txn_count_24h",
        "customer_prev_txn_count",
        "customer_prev_fraud_count",
        "customer_prev_fraud_rate",
        "merchant_prev_txn_count",
        "merchant_prev_fraud_count",
        "merchant_prev_fraud_rate",
        "geo_distance_from_last_txn",
        "account_age_days",
        "merchant_risk_score",
        "ip_risk_score",
        "is_international"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns required for feature engineering: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------------
    # DATETIME CONVERSION
    # --------------------------------------------------------

    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"],
        errors="coerce"
    )

    if df["transaction_time"].isna().any():
        raise ValueError(
            "Invalid transaction_time found in input data."
        )

    # ========================================================
    # 1. TEMPORAL FEATURES
    # ========================================================

    df["hour"] = (
        df["transaction_time"].dt.hour
    )

    df["day_of_week"] = (
        df["transaction_time"].dt.dayofweek
    )

    df["day_of_month"] = (
        df["transaction_time"].dt.day
    )

    df["month"] = (
        df["transaction_time"].dt.month
    )

    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    # --------------------------------------------------------
    # Late-night transactions
    # 00:00 - 05:59
    # --------------------------------------------------------

    df["is_late_night"] = (
        (df["hour"] >= 0) &
        (df["hour"] < 6)
    ).astype(int)

    # --------------------------------------------------------
    # Evening transactions
    # 18:00 - 23:59
    # --------------------------------------------------------

    df["is_evening"] = (
        (df["hour"] >= 18) &
        (df["hour"] < 24)
    ).astype(int)

    # ========================================================
    # 2. TRANSACTION AMOUNT FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Transaction amount relative to monthly spending
    # --------------------------------------------------------

    df["amount_to_monthly_spend"] = (
        df["transaction_amount"]
        /
        (df["avg_monthly_spend"] + 1)
    )

    # --------------------------------------------------------
    # Absolute amount deviation
    # --------------------------------------------------------

    df["abs_amount_deviation"] = (
        df["amount_deviation_from_user_mean"].abs()
    )

    # --------------------------------------------------------
    # Relative amount deviation
    # --------------------------------------------------------

    df["relative_amount_deviation"] = (
        df["abs_amount_deviation"]
        /
        (df["avg_monthly_spend"] + 1)
    )

    # --------------------------------------------------------
    # High-value transaction
    # --------------------------------------------------------

    df["high_value_transaction"] = (
        df["amount_to_monthly_spend"] > 0.5
    ).astype(int)

    # ========================================================
    # 3. TRANSACTION VELOCITY FEATURES
    # ========================================================

    # --------------------------------------------------------
    # 1-hour activity compared with 24-hour activity
    # --------------------------------------------------------

    df["txn_velocity_ratio"] = (
        df["txn_count_1h"]
        /
        (df["txn_count_24h"] + 1)
    )

    # --------------------------------------------------------
    # Failed transaction ratio
    # --------------------------------------------------------

    df["failed_txn_ratio"] = (
        df["failed_txn_count_24h"]
        /
        (df["txn_count_24h"] + 1)
    )

    # --------------------------------------------------------
    # High velocity in 1 hour
    # --------------------------------------------------------

    df["high_velocity_1h"] = (
        df["txn_count_1h"] >= 4
    ).astype(int)

    # --------------------------------------------------------
    # High velocity in 24 hours
    # --------------------------------------------------------

    df["high_velocity_24h"] = (
        df["txn_count_24h"] >= 6
    ).astype(int)

    # --------------------------------------------------------
    # Multiple failed transactions
    # --------------------------------------------------------

    df["multiple_failures"] = (
        df["failed_txn_count_24h"] >= 2
    ).astype(int)

    # ========================================================
    # 4. CUSTOMER BEHAVIOR FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Customer activity
    # --------------------------------------------------------

    df["customer_activity_level"] = (
        df["customer_prev_txn_count"]
    )

    # --------------------------------------------------------
    # Customer fraud history
    # --------------------------------------------------------

    df["customer_has_fraud_history"] = (
        df["customer_prev_fraud_count"] > 0
    ).astype(int)

    # --------------------------------------------------------
    # Customer risk signal
    # --------------------------------------------------------

    df["customer_risk_signal"] = (
        df["customer_prev_fraud_rate"]
        *
        np.log1p(
            df["customer_prev_txn_count"]
        )
    )

    # ========================================================
    # 5. MERCHANT BEHAVIOR FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Merchant fraud history
    # --------------------------------------------------------

    df["merchant_has_fraud_history"] = (
        df["merchant_prev_fraud_count"] > 0
    ).astype(int)

    # --------------------------------------------------------
    # Merchant risk signal
    # --------------------------------------------------------

    df["merchant_risk_signal"] = (
        df["merchant_prev_fraud_rate"]
        *
        np.log1p(
            df["merchant_prev_txn_count"]
        )
    )

    # ========================================================
    # 6. GEOLOCATION FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Large geographic distance
    # --------------------------------------------------------

    df["large_geo_distance"] = (
        df["geo_distance_from_last_txn"] >= 100
    ).astype(int)

    # --------------------------------------------------------
    # Geographic distance normalized by account age
    # --------------------------------------------------------

    df["geo_distance_per_account_day"] = (
        df["geo_distance_from_last_txn"]
        /
        (df["account_age_days"] + 1)
    )

    # ========================================================
    # 7. EXTERNAL RISK SCORE FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Combined merchant + IP risk
    # --------------------------------------------------------

    df["combined_external_risk"] = (
        df["merchant_risk_score"]
        +
        df["ip_risk_score"]
    ) / 2

    # --------------------------------------------------------
    # Maximum external risk
    # --------------------------------------------------------

    df["max_external_risk"] = df[
        [
            "merchant_risk_score",
            "ip_risk_score"
        ]
    ].max(axis=1)

    # --------------------------------------------------------
    # Difference between IP and merchant risk
    # --------------------------------------------------------

    df["risk_score_difference"] = (
        df["ip_risk_score"]
        -
        df["merchant_risk_score"]
    ).abs()

    # ========================================================
    # 8. RISK INTERACTION FEATURES
    # ========================================================

    # --------------------------------------------------------
    # International transaction × IP risk
    # --------------------------------------------------------

    df["international_ip_risk"] = (
        df["is_international"]
        *
        df["ip_risk_score"]
    )

    # --------------------------------------------------------
    # International transaction × merchant risk
    # --------------------------------------------------------

    df["international_merchant_risk"] = (
        df["is_international"]
        *
        df["merchant_risk_score"]
    )

    # --------------------------------------------------------
    # International + high IP risk
    # --------------------------------------------------------

    df["international_high_risk"] = (
        (
            df["is_international"] == 1
        )
        &
        (
            df["ip_risk_score"] > 0.5
        )
    ).astype(int)

    # --------------------------------------------------------
    # Velocity × failed transactions
    # --------------------------------------------------------

    df["velocity_failed_risk"] = (
        df["txn_count_24h"]
        *
        (
            df["failed_txn_count_24h"] + 1
        )
    )

    # ========================================================
    # 9. HISTORICAL RISK INTERACTIONS
    # ========================================================

    # --------------------------------------------------------
    # Customer + merchant fraud signal
    # --------------------------------------------------------

    df["customer_merchant_fraud_signal"] = (
        df["customer_prev_fraud_rate"]
        +
        df["merchant_prev_fraud_rate"]
    )

    # --------------------------------------------------------
    # Total historical fraud count
    # --------------------------------------------------------

    df["historical_fraud_count"] = (
        df["customer_prev_fraud_count"]
        +
        df["merchant_prev_fraud_count"]
    )

    # --------------------------------------------------------
    # Total historical activity
    # --------------------------------------------------------

    df["historical_activity"] = (
        df["customer_prev_txn_count"]
        +
        df["merchant_prev_txn_count"]
    )

    # ========================================================
    # 10. COMPOSITE RISK SIGNALS
    # ========================================================

    # --------------------------------------------------------
    # Behavioral risk
    # --------------------------------------------------------

    df["behavioral_risk_signal"] = (
        df["failed_txn_ratio"]
        +
        df["customer_prev_fraud_rate"]
        +
        df["merchant_prev_fraud_rate"]
    )

    # --------------------------------------------------------
    # Overall transaction risk signal
    # --------------------------------------------------------

    df["transaction_risk_signal"] = (
        df["combined_external_risk"]
        +
        df["behavioral_risk_signal"]
        +
        df["international_ip_risk"]
    )

    # ========================================================
    # NUMERICAL CLEANING
    # ========================================================

    # Replace infinite values generated by divisions
    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return df


# ============================================================
# FEATURE LIST USED BY MODEL
# ============================================================

FINAL_MODEL_FEATURES = [

    "account_age_days",
    "credit_score_band",
    "kyc_level",
    "avg_monthly_spend",
    "merchant_risk_score",
    "transaction_amount",
    "payment_channel",
    "device_type",
    "is_international",
    "ip_risk_score",
    "txn_count_1h",
    "txn_count_24h",
    "failed_txn_count_24h",
    "geo_distance_from_last_txn",
    "amount_deviation_from_user_mean",

    "hour",
    "day_of_week",
    "day",
    "month",
    "is_weekend",

    "customer_prev_txn_count",
    "merchant_prev_txn_count",
    "customer_prev_fraud_count",
    "merchant_prev_fraud_count",
    "customer_prev_fraud_rate",
    "merchant_prev_fraud_rate",

    "customer_prev_avg_amount",
    "merchant_prev_avg_amount",

    "customer_amount_ratio",
    "merchant_amount_ratio",

    "customer_smoothed_fraud_rate",
    "merchant_smoothed_fraud_rate",

    "day_of_month",
    "is_late_night",
    "is_evening",

    "amount_to_monthly_spend",
    "abs_amount_deviation",
    "relative_amount_deviation",
    "high_value_transaction",

    "txn_velocity_ratio",
    "failed_txn_ratio",
    "high_velocity_1h",
    "high_velocity_24h",
    "multiple_failures",

    "customer_activity_level",
    "customer_has_fraud_history",
    "customer_risk_signal",

    "merchant_has_fraud_history",
    "merchant_risk_signal",

    "large_geo_distance",
    "geo_distance_per_account_day",

    "combined_external_risk",
    "max_external_risk",
    "risk_score_difference",

    "international_ip_risk",
    "international_merchant_risk",
    "international_high_risk",
    "velocity_failed_risk",

    "customer_merchant_fraud_signal",
    "historical_fraud_count",
    "historical_activity",

    "behavioral_risk_signal",
    "transaction_risk_signal"
]


# ============================================================
# SELECT FINAL MODEL FEATURES
# ============================================================

def select_model_features(df):
    """
    Select exactly the 63 features expected by the trained model.
    """

    df = df.copy()

    missing_features = [
        feature
        for feature in FINAL_MODEL_FEATURES
        if feature not in df.columns
    ]

    if missing_features:

        raise ValueError(
            "Missing model features: "
            + ", ".join(missing_features)
        )

    return df[FINAL_MODEL_FEATURES].copy()


# ============================================================
# FEATURE ENGINEERING + MODEL FEATURE SELECTION
# ============================================================

def prepare_model_features(df):
    """
    Complete feature-engineering pipeline.

    1. Create engineered features
    2. Select the exact 63 model features
    """

    engineered_df = create_engineered_features(df)

    model_df = select_model_features(
        engineered_df
    )

    return model_df


# ============================================================
# FEATURE INFORMATION
# ============================================================

def get_feature_names():
    """
    Return the final model feature names.
    """

    return FINAL_MODEL_FEATURES.copy()


def get_feature_count():
    """
    Return number of final model features.
    """

    return len(FINAL_MODEL_FEATURES)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("FEATURE ENGINEERING MODULE")
    print("=" * 60)

    print(
        f"Final model features: "
        f"{get_feature_count()}"
    )

    print("\nFeatures:")

    for index, feature in enumerate(
        FINAL_MODEL_FEATURES,
        start=1
    ):
        print(
            f"{index:02d}. {feature}"
        )

    print("=" * 60)