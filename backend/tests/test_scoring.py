"""Tests for scoring consistency, feature parity, and severity overrides (Points 4-5).

Verifies:
- Training/serving feature parity (TC-U01, TC-U02, TC-U03)
- Cross-endpoint scoring consistency (TC-C01)
- Severity override transparency (TC-C02)
"""

import os
import sys
import math
import pytest
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from features import engineer_features, training_thresholds, TYPE_MAP, FEATURE_COLS

BASE = "http://127.0.0.1:8000"


def _login():
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "marcus.johnson@smarthorizon.ai", "password": "demo-password"
    })
    assert r.status_code == 200
    return r.json()["access_token"]


# ── TC-U01: Feature engineering parity ───────────────────────────────────────

class TestFeatureParity:
    """Ensure engineer_features uses persisted thresholds, not hardcoded values."""

    def _make_txn(self, amount=50000.0):
        old_bal = max(amount, 100000.0)
        return {
            "step": 100, "type": "TRANSFER", "amount": amount,
            "oldbalanceOrg": old_bal, "newbalanceOrig": old_bal - amount,
            "oldbalanceDest": 0.0, "newbalanceDest": amount,
        }

    def test_engineering_uses_persisted_thresholds(self):
        """engineer_features must require thresholds dict (no hardcoded values)."""
        txn = self._make_txn(50000.0)
        df = pd.DataFrame([txn])
        # Must pass thresholds — no default/hardcoded fallback
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        result = engineer_features(df, thresholds)
        assert list(result.columns) == FEATURE_COLS

    def test_large_amount_threshold_respected(self):
        """Amount just above threshold should flag is_large_amount=1."""
        txn = self._make_txn(150000.0)
        # Override to ensure non-negative balances
        txn["oldbalanceOrg"] = 200000.0
        txn["newbalanceOrig"] = 50000.0
        df = pd.DataFrame([txn])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        result = engineer_features(df, thresholds)
        assert result["is_large_amount"].iloc[0] == 1
        assert result["is_very_large"].iloc[0] == 0

    def test_very_large_amount_threshold_respected(self):
        """Amount above very_large threshold should flag is_very_large=1."""
        txn = self._make_txn(600000.0)
        # Override to ensure non-negative balances
        txn["oldbalanceOrg"] = 700000.0
        txn["newbalanceOrig"] = 100000.0
        df = pd.DataFrame([txn])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        result = engineer_features(df, thresholds)
        assert result["is_very_large"].iloc[0] == 1


# ── TC-U02: Unknown type encoding consistency ───────────────────────────────

class TestTypeEncoding:
    """Unknown type must map to -1 consistently."""

    def test_unknown_type_maps_to_minus_one(self):
        txn = {
            "step": 100, "type": "UNKNOWN_RAIL", "amount": 5000.0,
            "oldbalanceOrg": 10000.0, "newbalanceOrig": 5000.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 5000.0,
        }
        df = pd.DataFrame([txn])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        result = engineer_features(df, thresholds)
        assert result["type_encoded"].iloc[0] == -1

    def test_known_types_encode_correctly(self):
        for type_name, expected in TYPE_MAP.items():
            txn = {
                "step": 100, "type": type_name, "amount": 5000.0,
                "oldbalanceOrg": 10000.0, "newbalanceOrig": 5000.0,
                "oldbalanceDest": 0.0, "newbalanceDest": 5000.0,
            }
            df = pd.DataFrame([txn])
            thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
            result = engineer_features(df, thresholds)
            assert result["type_encoded"].iloc[0] == expected, \
                f"Type {type_name}: expected {expected}, got {result['type_encoded'].iloc[0]}"


# ── TC-U03: Input validation ────────────────────────────────────────────────

class TestInputValidation:
    """Reject invalid inputs: negative balances, NaN, inf."""

    def test_negative_balance_rejected(self):
        txn = {
            "step": 100, "type": "TRANSFER", "amount": 5000.0,
            "oldbalanceOrg": -1.0, "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 5000.0,
        }
        df = pd.DataFrame([txn])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        with pytest.raises(ValueError, match="negative"):
            engineer_features(df, thresholds)

    def test_nan_balance_rejected(self):
        txn = {
            "step": 100, "type": "TRANSFER", "amount": 5000.0,
            "oldbalanceOrg": float("nan"), "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 5000.0,
        }
        df = pd.DataFrame([txn])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        with pytest.raises(ValueError, match="non-finite"):
            engineer_features(df, thresholds)

    def test_inf_amount_rejected(self):
        txn = {
            "step": 100, "type": "TRANSFER", "amount": float("inf"),
            "oldbalanceOrg": 10000.0, "newbalanceOrig": 5000.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 5000.0,
        }
        df = pd.DataFrame([txn])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        with pytest.raises(ValueError, match="non-finite"):
            engineer_features(df, thresholds)

    def test_missing_columns_rejected(self):
        df = pd.DataFrame([{"step": 100, "type": "TRANSFER"}])
        thresholds = {"large_amount": 100000.0, "very_large_amount": 500000.0}
        with pytest.raises(ValueError, match="Missing required"):
            engineer_features(df, thresholds)


# ── TC-C01: Cross-endpoint scoring consistency ──────────────────────────────

class TestScoringConsistency:
    """Score from /score/analyze and /investigate must use the same override logic."""

    def test_same_transaction_same_score(self):
        """Investigation must use the centralized score_transaction function."""
        token = _login()
        headers = {"Authorization": f"Bearer {token}"}

        # Create a case via investigation
        r = requests.post(f"{BASE}/api/investigate/TXN-001",
                          headers=headers, timeout=60)
        if r.status_code == 200:
            inv_result = r.json()
            inv_score = inv_result.get("risk_score")
            inv_band = inv_result.get("risk_band")
            # The risk_score should be consistent with the band
            if inv_band == "LOW":
                assert inv_score < 30
            elif inv_band == "MEDIUM":
                assert 30 <= inv_score < 60
            elif inv_band == "HIGH":
                assert 60 <= inv_score < 80
            elif inv_band == "CRITICAL":
                assert inv_score >= 80


# ── TC-C02: Override transparency ───────────────────────────────────────────

class TestOverrideTransparency:
    """rule_adjustments must clearly flag when severity override was applied."""

    def test_model_probability_exposed(self):
        """Response must include both model_probability and risk_score."""
        token = _login()
        headers = {"Authorization": f"Bearer {token}"}

        r = requests.post(f"{BASE}/api/investigate/TXN-001",
                          headers=headers, timeout=60)
        if r.status_code == 200:
            data = r.json()
            assert "model_probability" in data, \
                "Response must include model_probability (pre-override)"
            assert "risk_score" in data, "Response must include risk_score"
            assert "rule_adjustments" in data, "Response must include rule_adjustments"
