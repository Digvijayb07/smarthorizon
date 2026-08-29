import sqlite3
import pickle
import json
import pandas as pd
from train_model import predict_transaction

with open("fraud_model.pkl", "rb") as f:
    model = pickle.load(f)

conn = sqlite3.connect("horizon.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM transactions WHERE is_fraud=1 GROUP BY scenario_type")
rows = c.fetchall()

print(f"{'Scenario Type':<30} | {'Amount':<12} | {'Risk Score':<10} | {'Band':<8} | {'Top Factor'}")
print("-" * 80)
for r in rows:
    txn = {
        "step": r["step"],
        "type": r["type"],
        "amount": r["amount"],
        "oldbalanceOrg": r["old_balance_orig"],
        "newbalanceOrig": r["new_balance_orig"],
        "oldbalanceDest": r["old_balance_dest"],
        "newbalanceDest": r["new_balance_dest"]
    }
    res = predict_transaction(model, txn)
    top_f = res["top_factors"][0]["feature"] if res["top_factors"] else "N/A"
    print(f"{r['scenario_type']:<30} | {r['amount']:<12,.0f} | {res['risk_score']:<10.1f} | {res['risk_band']:<8} | {top_f}")

conn.close()
