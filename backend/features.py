"""Canonical fraud-model features shared by training and inference."""

import math
import numpy as np
import pandas as pd

FEATURE_COLS = [
    "step", "type_encoded", "amount", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
    "balance_diff_orig", "balance_diff_dest", "error_balance_orig",
    "error_balance_dest", "amount_to_orig_ratio", "amount_to_dest_ratio",
    "orig_balance_zeroed", "dest_was_zero", "is_large_amount", "is_very_large",
    "step_mod_24", "is_night_txn", "is_transfer", "is_cashout",
    "dest_unchanged", "amount_dest_balance_ratio",
]

# Shared type encoding: must be identical in training and inference.
# Unknown types map to -1 (not a valid class for the model, but consistent).
TYPE_MAP = {
    "CASH_OUT": 0,
    "PAYMENT": 1,
    "CASH_IN": 2,
    "TRANSFER": 3,
    "DEBIT": 4,
}


def training_thresholds(df: pd.DataFrame) -> dict[str, float]:
    """Compute percentile-based thresholds from training data."""
    return {
        "large_amount": float(df["amount"].quantile(0.90)),
        "very_large_amount": float(df["amount"].quantile(0.99)),
    }


def engineer_features(df: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    """Engineer model features from raw transaction data.

    Thresholds MUST come from model_metadata.json (persisted at training time)
    to guarantee training/serving parity.

    Raises ValueError for invalid inputs: negative balances, non-finite values,
    or missing required columns.
    """
    fe = df.copy()

    required = [
        "step", "type", "amount",
        "oldbalanceOrg", "newbalanceOrig",
        "oldbalanceDest", "newbalanceDest",
    ]
    missing = [col for col in required if col not in fe]
    if missing:
        raise ValueError(f"Missing required feature fields: {', '.join(missing)}")

    # Validate numeric fields: must be finite and non-negative
    numeric = [col for col in required if col != "type"]
    for col in numeric:
        values = fe[col].astype(float)
        if not np.isfinite(values).all():
            raise ValueError(f"Column '{col}' contains non-finite values (NaN/inf)")
        if (values < 0).any():
            raise ValueError(f"Column '{col}' contains negative values")

    # Type encoding: unknown types map to -1 (consistent between train and serve)
    fe["type_encoded"] = fe["type"].map(TYPE_MAP).fillna(-1).astype(int)

    # Balance differences
    fe["balance_diff_orig"] = fe["oldbalanceOrg"] - fe["newbalanceOrig"]
    fe["balance_diff_dest"] = fe["newbalanceDest"] - fe["oldbalanceDest"]

    # Balance reconciliation errors
    fe["error_balance_orig"] = (fe["oldbalanceOrg"] - fe["newbalanceOrig"] - fe["amount"]).abs()
    fe["error_balance_dest"] = (fe["oldbalanceDest"] + fe["amount"] - fe["newbalanceDest"]).abs()

    # Ratios (safe division: denominator + 1.0 avoids division by zero)
    fe["amount_to_orig_ratio"] = fe["amount"] / (fe["oldbalanceOrg"] + 1.0)
    fe["amount_to_dest_ratio"] = fe["amount"] / (fe["oldbalanceDest"] + 1.0)

    # Binary flags
    fe["orig_balance_zeroed"] = (fe["newbalanceOrig"] == 0).astype(int)
    fe["dest_was_zero"] = (fe["oldbalanceDest"] == 0).astype(int)

    # Threshold flags — thresholds come from persisted model_metadata.json
    fe["is_large_amount"] = (fe["amount"] > thresholds["large_amount"]).astype(int)
    fe["is_very_large"] = (fe["amount"] > thresholds["very_large_amount"]).astype(int)

    # Time features
    fe["step_mod_24"] = fe["step"] % 24
    fe["is_night_txn"] = ((fe["step_mod_24"] >= 22) | (fe["step_mod_24"] <= 5)).astype(int)

    # Type flags
    fe["is_transfer"] = (fe["type"] == "TRANSFER").astype(int)
    fe["is_cashout"] = (fe["type"] == "CASH_OUT").astype(int)

    # Balance behavior
    fe["dest_unchanged"] = (fe["balance_diff_dest"] == 0).astype(int)
    fe["amount_dest_balance_ratio"] = fe["amount"] / (fe["newbalanceDest"] + 1.0)

    return fe[FEATURE_COLS]
