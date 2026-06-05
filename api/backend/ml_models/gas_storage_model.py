import math


def predict_risk(weights, storage_at_start, storage_trend_30d, storage_volatility):
    # standardize inputs with the scaler params learned at training time
    x1 = (storage_at_start   - weights["mean_storage_at_start"])   / weights["std_storage_at_start"]
    x2 = (storage_trend_30d  - weights["mean_storage_trend_30d"])  / weights["std_storage_trend_30d"]
    x3 = (storage_volatility - weights["mean_storage_volatility"]) / weights["std_storage_volatility"]

    z = (
        weights["intercept"]
        + weights["weight_storage_at_start"] * x1
        + weights["weight_storage_trend_30d"] * x2
        + weights["weight_storage_volatility"] * x3
    )
    risk_prob = 1.0 / (1.0 + math.exp(-z))
    return {
        "at_risk": risk_prob >= 0.5,
        "risk_prob": risk_prob,
    }
