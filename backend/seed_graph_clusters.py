"""
Seed Graph Clusters — Enrich database with realistic multi-hop fraud topologies.
Schema:
['transaction_id', 'case_id', 'sender_id', 'sender_account', 'receiver_id', 'receiver_account', 
 'amount', 'channel', 'step', 'type', 'old_balance_orig', 'new_balance_orig', 'old_balance_dest', 
 'new_balance_dest', 'timestamp', 'device_id', 'ip_address', 'location_city', 'is_new_payee', 
 'is_vpn', 'fraud_type', 'is_fraud', 'alert_triggered', 'scenario_type', 'fraud_reason', 'severity']
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "horizon.db")

def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.now()

    # --------------------------------------------------------------------------
    # 1. Cluster for FC-20260815-8E916E (Canara-36480482 -> Kotak-74333786)
    # --------------------------------------------------------------------------
    base_time = now - timedelta(hours=3)
    
    feeder_and_mule_txns = [
        # Upstream Feeders -> Canara-36480482
        (
            "TXN-FEEDER-01", "FC-20260815-8E916E",
            "CUST-FEEDER-1", "SBI-91028312",
            "CUST-36480482", "Canara-36480482",
            95000.0, "IMPS", 1, "TRANSFER",
            120000.0, 25000.0, 5000.0, 100000.0,
            (base_time - timedelta(minutes=25)).isoformat(),
            "DEV-F01", "103.21.244.11", "Mumbai",
            0, 0, "AGGREGATION_FEEDER", 0, 0,
            "AGGREGATION_FEEDER", "Feeder transfer pooling funds into syndicate origin", "LOW"
        ),
        (
            "TXN-FEEDER-02", "FC-20260815-8E916E",
            "CUST-FEEDER-2", "HDFC-11209485",
            "CUST-36480482", "Canara-36480482",
            100000.0, "NEFT", 2, "TRANSFER",
            150000.0, 50000.0, 100000.0, 200000.0,
            (base_time - timedelta(minutes=15)).isoformat(),
            "DEV-F02", "103.21.244.12", "Delhi",
            0, 0, "AGGREGATION_FEEDER", 0, 0,
            "AGGREGATION_FEEDER", "Feeder transfer pooling funds into syndicate origin", "LOW"
        ),
        # Downstream Mule Fan-Out from Kotak-74333786
        (
            "TXN-MULE-01", "FC-20260815-8E916E",
            "CUST-74333786", "Kotak-74333786",
            "CUST-MULE-1", "Axis-55019283",
            58000.0, "UPI", 3, "TRANSFER",
            181684.0, 123684.0, 1200.0, 59200.0,
            (base_time + timedelta(minutes=4)).isoformat(),
            "DEV-M01", "45.112.55.10", "Surat",
            1, 1, "MULE_DISPERSION", 1, 1,
            "MULE_DISPERSION", "Rapid fan-out mule dispersion following major inward credit", "HIGH"
        ),
        (
            "TXN-MULE-02", "FC-20260815-8E916E",
            "CUST-74333786", "Kotak-74333786",
            "CUST-MULE-2", "ICICI-88192039",
            62000.0, "UPI", 4, "TRANSFER",
            123684.0, 61684.0, 500.0, 62500.0,
            (base_time + timedelta(minutes=6)).isoformat(),
            "DEV-M02", "45.112.55.11", "Ahmedabad",
            1, 1, "MULE_DISPERSION", 1, 1,
            "MULE_DISPERSION", "Rapid fan-out mule dispersion following major inward credit", "HIGH"
        ),
        (
            "TXN-MULE-03", "FC-20260815-8E916E",
            "CUST-74333786", "Kotak-74333786",
            "CUST-MULE-3", "Paytm-99018274",
            60000.0, "UPI", 5, "TRANSFER",
            61684.0, 1684.0, 200.0, 60200.0,
            (base_time + timedelta(minutes=8)).isoformat(),
            "DEV-M03", "45.112.55.12", "Jaipur",
            1, 1, "MULE_DISPERSION", 1, 1,
            "MULE_DISPERSION", "Account draining cashout through third mule account", "CRITICAL"
        ),
    ]

    for t in feeder_and_mule_txns:
        c.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, case_id, sender_id, sender_account,
                receiver_id, receiver_account, amount, channel, step, type,
                old_balance_orig, new_balance_orig, old_balance_dest, new_balance_dest,
                timestamp, device_id, ip_address, location_city,
                is_new_payee, is_vpn, fraud_type, is_fraud, alert_triggered,
                scenario_type, fraud_reason, severity
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, t)

    # --------------------------------------------------------------------------
    # 2. Structuring / Smurfing Case: FC-20260904-STR01
    # --------------------------------------------------------------------------
    struct_sender = "HDFC-44344942"
    struct_time = now - timedelta(hours=1)
    
    structuring_txns = [
        ("TXN-STR-01", struct_sender, "Axis-20152485", 48500.0, 0),
        ("TXN-STR-02", struct_sender, "ICICI-63650963", 49200.0, 2),
        ("TXN-STR-03", struct_sender, "BOB-85021338", 47800.0, 4),
        ("TXN-STR-04", struct_sender, "Canara-85484212", 46900.0, 7),
    ]

    for tx_id, s_acc, r_acc, amt, offset_min in structuring_txns:
        c.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, case_id, sender_id, sender_account,
                receiver_id, receiver_account, amount, channel, step, type,
                old_balance_orig, new_balance_orig, old_balance_dest, new_balance_dest,
                timestamp, device_id, ip_address, location_city,
                is_new_payee, is_vpn, fraud_type, is_fraud, alert_triggered,
                scenario_type, fraud_reason, severity
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tx_id, "FC-20260904-STR01",
            "CUST-STR-S", s_acc,
            f"CUST-STR-R{offset_min}", r_acc,
            amt, "UPI", offset_min, "TRANSFER",
            200000.0, 200000.0 - amt, 1000.0, 1000.0 + amt,
            (struct_time + timedelta(minutes=offset_min)).isoformat(),
            "DEV-STR01", "185.220.101.5", "Bengaluru",
            1, 1, "STRUCTURING", 1, 1,
            "STRUCTURING",
            "Multiple sub-50,000 INR transfers in under 10 minutes to evade PMLA threshold",
            "CRITICAL"
        ))

    # Add case for structuring
    c.execute("""
        INSERT OR REPLACE INTO cases (
            case_id, transaction_id, status, risk_score, risk_band, recommended_action,
            analyst_id, opened_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "FC-20260904-STR01", "TXN-STR-01", "OPEN", 98.4, "CRITICAL", "ESCALATE",
        "INV-CURRENT", struct_time.isoformat(), struct_time.isoformat()
    ))

    # --------------------------------------------------------------------------
    # 3. Circular Flow Case: FC-20260904-CIRC01
    # --------------------------------------------------------------------------
    circ_time = now - timedelta(hours=2)
    circular_txns = [
        ("TXN-CIRC-01", "Axis-36480482", "PNB-91699287", 813608.0, 0),
        ("TXN-CIRC-02", "PNB-91699287", "Canara-84073862", 810000.0, 5),
        ("TXN-CIRC-03", "Canara-84073862", "Axis-36480482", 805000.0, 11),
    ]

    for tx_id, s_acc, r_acc, amt, offset_min in circular_txns:
        c.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, case_id, sender_id, sender_account,
                receiver_id, receiver_account, amount, channel, step, type,
                old_balance_orig, new_balance_orig, old_balance_dest, new_balance_dest,
                timestamp, device_id, ip_address, location_city,
                is_new_payee, is_vpn, fraud_type, is_fraud, alert_triggered,
                scenario_type, fraud_reason, severity
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tx_id, "FC-20260904-CIRC01",
            f"CUST-{s_acc}", s_acc,
            f"CUST-{r_acc}", r_acc,
            amt, "RTGS", offset_min, "TRANSFER",
            900000.0, 900000.0 - amt, 50000.0, 50000.0 + amt,
            (circ_time + timedelta(minutes=offset_min)).isoformat(),
            "DEV-CIRC", "192.168.1.1", "Mumbai",
            0, 0, "CIRCULAR_TRANSACTIONS", 1, 1,
            "CIRCULAR_TRANSACTIONS",
            "Closed loop fund cycling detected across 3 accounts (Round-tripping)",
            "CRITICAL"
        ))

    c.execute("""
        INSERT OR REPLACE INTO cases (
            case_id, transaction_id, status, risk_score, risk_band, recommended_action,
            analyst_id, opened_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "FC-20260904-CIRC01", "TXN-CIRC-01", "OPEN", 99.2, "CRITICAL", "ESCALATE",
        "INV-CURRENT", circ_time.isoformat(), circ_time.isoformat()
    ))

    conn.commit()
    conn.close()
    print("Successfully seeded multi-hop clusters, structuring case, and circular cycle!")

if __name__ == "__main__":
    seed()
