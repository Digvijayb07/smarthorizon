import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/paysim_base_128k.csv"
OUTPUT_FILE = "data/synthetic_S04_new_beneficiary.csv"

TARGET_ROWS = 4000
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Base dataset:", df.shape)

# ============================================================
# LEGITIMATE TRANSACTIONS
# ============================================================

legit = df[
    df["isFraud"] == 0
].copy()

print(
    "Legitimate transactions:",
    len(legit)
)

# We need senders that have some transaction history.
# Their previous destinations become their "known"
# beneficiaries.

sender_history = (
    legit
    .groupby("nameOrig")
    .agg(
        transaction_count=("record_id", "count"),
        unique_destinations=("nameDest", "nunique"),
        avg_amount=("amount", "mean"),
        median_amount=("amount", "median"),
        max_amount=("amount", "max"),
        max_balance=("oldbalanceOrg", "max")
    )
    .reset_index()
)

# Keep senders with at least 2 historical transactions
eligible_senders = sender_history[
    (sender_history["transaction_count"] >= 1) &
    (sender_history["unique_destinations"] >= 1) &
    (sender_history["max_balance"] > 0)
].copy()

print(
    "Eligible senders:",
    len(eligible_senders)
)

if len(eligible_senders) == 0:
    raise ValueError(
        "No senders with sufficient transaction history found."
    )

# ============================================================
# BUILD KNOWN BENEFICIARY MAP
# ============================================================

known_beneficiaries = (
    legit
    .groupby("nameOrig")["nameDest"]
    .apply(set)
    .to_dict()
)

# ============================================================
# GENERATE S04
# ============================================================

synthetic_rows = []

scenario_number = 1

while len(synthetic_rows) < TARGET_ROWS:

    # --------------------------------------------------------
    # Select sender with historical activity
    # --------------------------------------------------------

    sender_info = eligible_senders.sample(
        n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    sender = sender_info["nameOrig"]

    # Select an actual historical transaction for this sender
    sender_history_rows = legit[
        legit["nameOrig"] == sender
    ]

    seed = sender_history_rows.sample(
    n=1,
        random_state=np.random.randint(
            0,
            1_000_000
        )
    ).iloc[0]

    known_destinations = known_beneficiaries.get(
        sender,
        set()
    )

    # --------------------------------------------------------
    # Generate a genuinely NEW beneficiary
    # --------------------------------------------------------

    new_destination = None

    for _ in range(100):

        candidate = (
            "C_SYN_" +
            str(
                np.random.randint(
                    100000000,
                    999999999
                )
            )
        )

        if candidate not in known_destinations:
            new_destination = candidate
            break

    if new_destination is None:
        continue

    # --------------------------------------------------------
    # Historical amount behavior
    # --------------------------------------------------------

    historical_median = float(
        sender_info["median_amount"]
    )

    historical_max = float(
        sender_info["max_amount"]
    )

    # Avoid tiny/zero values
    historical_median = max(
        historical_median,
        10000
    )

    historical_max = max(
        historical_max,
        historical_median
    )

    # --------------------------------------------------------
    # Generate unusually large transaction
    # --------------------------------------------------------

    suspicious_amount = max(
        historical_max *
        np.random.uniform(
            1.5,
            2.5
        ),

        historical_median *
        np.random.uniform(
            3.0,
            6.0
        )
    )

    suspicious_amount = round(
        suspicious_amount,
        2
    )

    # --------------------------------------------------------
    # Create sufficient balance
    # --------------------------------------------------------

    # Keep this below account-draining territory.
    # This scenario should primarily be:
    #
    # NEW BENEFICIARY + LARGE AMOUNT
    #
    starting_balance = (
        suspicious_amount *
        np.random.uniform(
            2.0,
            3.0
        )
    )

    old_balance = starting_balance

    new_balance = (
        old_balance -
        suspicious_amount
    )

    # --------------------------------------------------------
    # Transaction type
    # --------------------------------------------------------

    transaction_type = "TRANSFER"

    # --------------------------------------------------------
    # Generate transaction
    # --------------------------------------------------------

    row = {

        # -----------------------------
        # PaySim fields
        # -----------------------------

        "record_id":
            f"S04_{len(synthetic_rows)+1:06d}",

        "step":
            int(seed["step"]) +
            np.random.randint(1, 10),

        "type":
            transaction_type,

        "amount":
            suspicious_amount,

        "nameOrig":
            sender,

        "oldbalanceOrg":
            round(
                old_balance,
                2
            ),

        "newbalanceOrig":
            round(
                new_balance,
                2
            ),

        "nameDest":
            new_destination,

        "oldbalanceDest":
            0.0,

        "newbalanceDest":
            round(
                suspicious_amount,
                2
            ),

        "isFraud":
            1,

        "isFlaggedFraud":
            0,

        # -----------------------------
        # Investigator metadata
        # -----------------------------

        "scenario_id":
            f"S04_{scenario_number:05d}",

        "scenario_type":
            "NEW_BENEFICIARY_LARGE_TRANSFER",

        "fraud_reason":
            "Large transfer sent to a previously unseen beneficiary",

        "severity":
            "HIGH",

        # Useful investigation features
        "is_new_beneficiary":
            1,

        "historical_max_amount":
            round(
                historical_max,
                2
            ),

        "amount_vs_historical_max":
            round(
                suspicious_amount /
                historical_max,
                2
            )
    }

    synthetic_rows.append(row)

    scenario_number += 1

# ============================================================
# DATAFRAME
# ============================================================

synthetic = pd.DataFrame(
    synthetic_rows
)

synthetic = synthetic.head(
    TARGET_ROWS
)

# ============================================================
# VALIDATION METRICS
# ============================================================

synthetic["balance_usage_ratio"] = (
    synthetic["amount"] /
    synthetic["oldbalanceOrg"]
)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("S04 VALIDATION")
print("=" * 60)

print(
    "Rows:",
    len(synthetic)
)

print(
    "Fraud labels:",
    synthetic["isFraud"]
    .value_counts()
    .to_dict()
)

print(
    "Transaction types:",
    synthetic["type"]
    .value_counts()
    .to_dict()
)

print(
    "Unique accounts:",
    synthetic["nameOrig"]
    .nunique()
)

print(
    "Unique scenarios:",
    synthetic["scenario_id"]
    .nunique()
)

print(
    "New beneficiary rate:",
    round(
        synthetic["is_new_beneficiary"].mean() * 100,
        2
    ),
    "%"
)

print(
    "Average amount:",
    round(
        synthetic["amount"].mean(),
        2
    )
)

print(
    "Median amount:",
    round(
        synthetic["amount"].median(),
        2
    )
)

print(
    "Minimum amount:",
    round(
        synthetic["amount"].min(),
        2
    )
)

print(
    "Maximum amount:",
    round(
        synthetic["amount"].max(),
        2
    )
)

print(
    "Average amount / historical max:",
    round(
        synthetic[
            "amount_vs_historical_max"
        ].mean(),
        2
    ),
    "x"
)

print(
    "Average balance usage:",
    round(
        synthetic[
            "balance_usage_ratio"
        ].mean() * 100,
        2
    ),
    "%"
)

# ============================================================
# VALIDATION CHECKS
# ============================================================

assert len(synthetic) == TARGET_ROWS

assert (
    synthetic["isFraud"] == 1
).all()

assert (
    synthetic["type"] == "TRANSFER"
).all()

assert (
    synthetic["is_new_beneficiary"] == 1
).all()

assert (
    synthetic["scenario_type"] ==
    "NEW_BENEFICIARY_LARGE_TRANSFER"
).all()

assert (
    synthetic["scenario_id"]
    .nunique()
    == TARGET_ROWS
)

# Ensure transaction does not normally represent
# account draining.
assert (
    synthetic["balance_usage_ratio"] < 0.80
).all()

# Ensure transaction is substantially larger
# than sender's historical maximum.
assert (
    synthetic["amount_vs_historical_max"] > 1.0
).all()

# ============================================================
# SAVE
# ============================================================

synthetic.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(
    "Saved:",
    OUTPUT_FILE
)

print(
    "Final shape:",
    synthetic.shape
)

print()
print("Sample:")

print(
    synthetic[
        [
            "record_id",
            "step",
            "type",
            "amount",
            "nameOrig",
            "nameDest",
            "isFraud",
            "scenario_id",
            "scenario_type",
            "severity",
            "is_new_beneficiary",
            "historical_max_amount",
            "amount_vs_historical_max"
        ]
    ].head(10)
)