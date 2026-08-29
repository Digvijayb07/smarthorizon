"""
scoreAgent Router -- /api/score/analyze
=======================================
Takes a raw transaction, runs XGBoost + SHAP,
returns risk score + explainability breakdown.

This is Agent 1 in the 4-agent pipeline.
"""

import pickle
import json
import shap
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from state import app_state

router = APIRouter()

class TransactionInput(BaseModel):
    transaction_id:   str
    step:             int   = 1
    type:             str   = "TRANSFER"
    amount:           float
    nameOrig:         str   = "UNKNOWN"
    oldbalanceOrg:    float = 0.0
    newbalanceOrig:   float = 0.0
    nameDest:         str   = "UNKNOWN"
    oldbalanceDest:   float = 0.0
    newbalanceDest:   float = 0.0
    # Optional enrichment fields
    is_new_payee:     Optional[bool]  = False
    is_vpn:           Optional[bool]  = False
    location_city:    Optional[str]   = "Unknown"
    device_id:        Optional[str]   = None
    ip_address:       Optional[str]   = None
    scenario_type:    Optional[str]   = None
    fraud_reason:     Optional[str]   = None
    severity:         Optional[str]   = "NONE"

class ScoreResponse(BaseModel):
    transaction_id: str
    risk_score:     float       # 0-100
    risk_band:      str         # LOW / MEDIUM / HIGH / CRITICAL
    probability:    float       # raw model probability
    recommended_action: str     # ALLOW / MONITOR / FLAG / BLOCK
    top_factors:    list
    shap_values:    dict
    model_version:  str

FEATURE_COLS = [
    "step", "type_encoded", "amount",
    "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest",
    "balance_diff_orig", "balance_diff_dest",
    "error_balance_orig", "error_balance_dest",
    "amount_to_orig_ratio", "amount_to_dest_ratio",
    "orig_balance_zeroed", "dest_was_zero",
    "is_large_amount", "is_very_large",
    "step_mod_24", "is_night_txn",
    "is_transfer", "is_cashout", "dest_unchanged",
    "amount_dest_balance_ratio"
]

TYPE_MAP = {"CASH_OUT": 0, "PAYMENT": 1, "CASH_IN": 2, "TRANSFER": 3, "DEBIT": 4}

def _engineer(txn: dict) -> pd.DataFrame:
    df = pd.DataFrame([txn])
    df["type_encoded"]         = df["type"].map(TYPE_MAP).fillna(3).astype(int)
    df["balance_diff_orig"]    = df["oldbalanceOrg"]  - df["newbalanceOrig"]
    df["balance_diff_dest"]    = df["newbalanceDest"] - df["oldbalanceDest"]
    df["error_balance_orig"]   = (df["oldbalanceOrg"] - df["newbalanceOrig"] - df["amount"]).abs()
    df["error_balance_dest"]   = (df["oldbalanceDest"] + df["amount"] - df["newbalanceDest"]).abs()
    df["amount_to_orig_ratio"] = df["amount"] / (df["oldbalanceOrg"] + 1.0)
    df["amount_to_dest_ratio"] = df["amount"] / (df["oldbalanceDest"] + 1.0)
    df["orig_balance_zeroed"]  = (df["newbalanceOrig"] == 0).astype(int)
    df["dest_was_zero"]        = (df["oldbalanceDest"] == 0).astype(int)

    df["is_large_amount"]      = (df["amount"] > 200_000).astype(int)
    df["is_very_large"]        = (df["amount"] > 1_000_000).astype(int)
    df["step_mod_24"]          = df["step"] % 24
    df["is_night_txn"]         = ((df["step_mod_24"] >= 22) | (df["step_mod_24"] <= 5)).astype(int)
    df["is_transfer"]          = (df["type"] == "TRANSFER").astype(int)
    df["is_cashout"]           = (df["type"] == "CASH_OUT").astype(int)
    df["dest_unchanged"]       = (df["balance_diff_dest"] == 0).astype(int)
    df["amount_dest_balance_ratio"] = df["amount"] / (df["newbalanceDest"] + 1.0)
    return df[FEATURE_COLS]

def _action_from_band(band: str) -> str:
    return {
        "LOW":      "ALLOW",
        "MEDIUM":   "MONITOR",
        "HIGH":     "FLAG",
        "CRITICAL": "BLOCK",
    }.get(band, "MONITOR")

@router.post("/analyze", response_model=ScoreResponse)
async def analyze_transaction(txn: TransactionInput):
    """
    scoreAgent: Run fraud risk scoring on a single transaction.
    Returns risk score 0-100 with SHAP feature attribution.
    """
    if app_state.model is None:
        raise HTTPException(503, "Fraud model not loaded. Run train_enhanced_model.py first.")

    model    = app_state.model
    metadata = app_state.metadata or {}

    try:
        X = _engineer(txn.model_dump())
    except Exception as e:
        raise HTTPException(400, f"Feature engineering failed: {str(e)}")

    proba = float(model.predict_proba(X)[0, 1])

    # Severity/Scenario hybrid calibration
    # If the transaction triggered a high/critical scenario alert, ensure high sensitivity
    if txn.severity == "CRITICAL" and proba < 0.80:
        proba = max(proba, 0.85)
    elif txn.severity == "HIGH" and proba < 0.60:
        proba = max(proba, 0.68)

    if proba < 0.30:
        band = "LOW"
    elif proba < 0.60:
        band = "MEDIUM"
    elif proba < 0.80:
        band = "HIGH"
    else:
        band = "CRITICAL"

    explainer   = shap.TreeExplainer(model)
    shap_vals   = explainer.shap_values(X)[0]
    shap_dict   = {f: round(float(v), 4) for f, v in zip(FEATURE_COLS, shap_vals)}

    feat_desc = metadata.get("feature_descriptions", {})
    top_factors = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    factors_out = [
        {
            "feature":     k,
            "shap_value":  v,
            "impact":      "increases_risk" if v > 0 else "decreases_risk",
            "description": feat_desc.get(k, k),
        }
        for k, v in top_factors
    ]

    return ScoreResponse(
        transaction_id    = txn.transaction_id,
        risk_score        = round(proba * 100, 1),
        risk_band         = band,
        probability       = round(proba, 4),
        recommended_action= _action_from_band(band),
        top_factors       = factors_out,
        shap_values       = shap_dict,
        model_version     = "xgboost-enhanced-v2.0",
    )
